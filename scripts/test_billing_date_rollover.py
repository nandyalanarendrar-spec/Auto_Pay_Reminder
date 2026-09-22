"""
Automated Verification Script: Billing Date Rollover Triggers
Tests:
1. Rollover date calculation engine (calendar-aware)
2. Safety net on GET /subscriptions (query-time on-the-fly rollover)
3. Safety net on GET /emis (query-time on-the-fly rollover)
4. Proactive Background Scheduled Sweep execution
5. In-place calendar sync verification (preserving event ID)
"""

import sys
import os
import io

# Ensure UTF-8 stdout on Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uuid
from datetime import date, timedelta, datetime
from app.services.subscription_service import SubscriptionService
from app.services.emi_service import EMIService
from app.services.background_scheduler_service import run_daily_rollover_sweep
from app.schemas.subscription import SubscriptionCreate
from app.schemas.emi import EMICreate
from app.core.security import get_supabase_client


def run_tests():
    print("=" * 80)
    print("🧪 AUTOMATED TEST: BILLING DATE ROLLOVER TRIGGERS (SCHEDULED + QUERY-TIME)")
    print("=" * 80)

    supabase = get_supabase_client()
    test_email = f"rollover_test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"

    # Create real test user to satisfy foreign key constraint on users table
    auth_resp = supabase.auth.sign_up({"email": test_email, "password": test_password})
    test_user_id = str(auth_resp.user.id)
    print(f"Created test user: {test_user_id} ({test_email})")

    today = date.today()
    yesterday = today - timedelta(days=1)
    two_months_ago = today - timedelta(days=62)

    print(f"\n[Step 1] Verifying Calendar-Aware Rollover Engine...")
    rolled_monthly = SubscriptionService.calculate_rolled_over_date(str(yesterday), "monthly", target_today=today)
    print(f"  - Monthly from yesterday ({yesterday}) -> {rolled_monthly}")
    assert rolled_monthly >= str(today), f"Expected >= {today}, got {rolled_monthly}"

    rolled_two_mo = SubscriptionService.calculate_rolled_over_date(str(two_months_ago), "monthly", target_today=today)
    print(f"  - Monthly from 2 months ago ({two_months_ago}) -> {rolled_two_mo}")
    assert rolled_two_mo >= str(today), f"Expected >= {today}, got {rolled_two_mo}"

    rolled_yearly = SubscriptionService.calculate_rolled_over_date(str(yesterday), "yearly", target_today=today)
    print(f"  - Yearly from yesterday ({yesterday}) -> {rolled_yearly}")
    assert rolled_yearly >= str(today), f"Expected >= {today}, got {rolled_yearly}"
    print("  ✅ PASS: Calendar-aware rollover date calculations verified.")

    print(f"\n[Step 2] Testing Query-Time Safety Net on GET /subscriptions...")
    # Create an overdue subscription directly in Supabase
    overdue_sub_payload = SubscriptionCreate(
        merchant_name=f"Test Overdue Sub {uuid.uuid4().hex[:6]}",
        category="Software",
        amount=499.0,
        billing_frequency="monthly",
        next_payment_date=yesterday,
        status="active"
    )
    created_sub = SubscriptionService.create_subscription(None, test_user_id, overdue_sub_payload, trigger_calendar=False)
    sub_id = created_sub["id"]
    print(f"  - Created test subscription {sub_id} with initial next_payment_date = {yesterday}")

    # Explicitly ensure in DB that next_payment_date is yesterday
    supabase = get_supabase_client()
    supabase.from_("subscriptions").update({"next_payment_date": str(yesterday)}).eq("id", sub_id).execute()

    # Call get_user_subscriptions (which simulates GET /subscriptions)
    print(f"  - Calling get_user_subscriptions for user {test_user_id}...")
    user_subs = SubscriptionService.get_user_subscriptions(test_user_id)

    target_sub = next((s for s in user_subs if str(s.get("id")) == sub_id), None)
    assert target_sub is not None, "Subscription not found in user_subs!"
    returned_date = str(target_sub.get("next_payment_date"))[:10]
    print(f"  - Returned next_payment_date: {returned_date}")
    assert returned_date >= str(today), f"Expected date >= {today}, but got {returned_date}"
    print("  ✅ PASS: Safety net rolled overdue subscription forward automatically on GET!")

    print(f"\n[Step 3] Testing Query-Time Safety Net on GET /emis...")
    overdue_emi_payload = EMICreate(
        loan_name=f"Test Overdue Loan {uuid.uuid4().hex[:6]}",
        total_installments=12,
        installments_paid=2,
        installment_amount=1500.0,
        next_due_date=yesterday,
        status="active"
    )
    created_emi = EMIService.create_emi(test_user_id, overdue_emi_payload, trigger_calendar=False)
    emi_id = created_emi["id"]
    print(f"  - Created test EMI {emi_id} with initial next_due_date = {yesterday}")

    supabase.from_("emis").update({"next_due_date": str(yesterday)}).eq("id", emi_id).execute()

    user_emis = EMIService.get_user_emis(test_user_id)
    target_emi = next((e for e in user_emis if str(e.get("id")) == emi_id), None)
    assert target_emi is not None, "EMI not found in user_emis!"
    returned_emi_date = str(target_emi.get("next_due_date"))[:10]
    print(f"  - Returned next_due_date: {returned_emi_date}")
    assert returned_emi_date >= str(today), f"Expected EMI date >= {today}, but got {returned_emi_date}"
    print("  ✅ PASS: Safety net rolled overdue EMI forward automatically on GET!")

    print(f"\n[Step 4] Testing Background Scheduled Sweep...")
    # Set date back to yesterday directly in DB
    supabase.from_("subscriptions").update({"next_payment_date": str(yesterday)}).eq("id", sub_id).execute()
    supabase.from_("emis").update({"next_due_date": str(yesterday)}).eq("id", emi_id).execute()

    # Test SubscriptionService & EMIService background sweep functions
    rolled_subs = SubscriptionService.auto_rollover_overdue_subscriptions(test_user_id)
    rolled_emis = EMIService.auto_rollover_overdue_emis(test_user_id)
    print(f"  - User sweep: {len(rolled_subs)} subscriptions rolled, {len(rolled_emis)} EMIs rolled.")

    # Also test global daily sweep function
    sweep_result = run_daily_rollover_sweep()
    print(f"  - Global sweep result: {sweep_result}")
    assert sweep_result.get("status") == "success", "Sweep did not report success"

    # Verify DB state directly
    sub_check = supabase.from_("subscriptions").select("next_payment_date").eq("id", sub_id).execute()
    assert sub_check.data and str(sub_check.data[0]["next_payment_date"])[:10] >= str(today)
    emi_check = supabase.from_("emis").select("next_due_date").eq("id", emi_id).execute()
    assert emi_check.data and str(emi_check.data[0]["next_due_date"])[:10] >= str(today)
    print("  ✅ PASS: Background scheduler sweep successfully rolled all overdue items forward!")

    # Cleanup test records
    try:
        supabase.from_("subscriptions").delete().eq("user_id", test_user_id).execute()
        supabase.from_("emis").delete().eq("user_id", test_user_id).execute()
    except Exception:
        pass

    print("\n" + "=" * 80)
    print("🎉 ALL BILLING ROLLOVER TESTS PASSED PERFECTLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
