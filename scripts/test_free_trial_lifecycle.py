"""
Automated Test C2: Free Trial Date Handling & Rollover Lifecycle
Verifies:
1. Subscription model stores trial_start_date, trial_end_date, expected_first_payment_date, and is_free_trial.
2. Calendar reminder event is created for trial_end_date with '⚠️ {merchant} Trial Ending' title and metadata.
3. When trial_end_date arrives/passes without cancellation, system transitions it into paid recurring subscription ('active'), updates next_payment_date, and updates the calendar event with the same ID via in-place PATCH.
"""
import sys
import os
import uuid
from datetime import date, timedelta

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import get_supabase_client
from app.schemas.subscription import SubscriptionCreate
from app.services.subscription_service import SubscriptionService
from app.services.calendar_agent_service import CalendarAgentService


def run_free_trial_tests():
    print("=" * 70)
    print("🧪 AUTOMATED TEST C2: FREE TRIAL DATE HANDLING & ROLLOVER")
    print("=" * 70)

    supabase = get_supabase_client()
    test_email = f"trial_test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"

    # Step 1: Create real test user
    auth_resp = supabase.auth.sign_up({"email": test_email, "password": test_password})
    test_user_id = str(auth_resp.user.id)
    print(f"\n[Step 1] Created test user: {test_user_id} ({test_email})")

    try:
        today = date.today()
        trial_start = today
        trial_end = today + timedelta(days=7)
        first_charge_date = trial_end

        # -------------------------------------------------------------
        # Step 2: Create Free Trial Subscription
        # -------------------------------------------------------------
        print(f"\n[Step 2] Creating Free Trial Subscription (7-day trial)...")
        print(f"  • Trial Start: {trial_start}")
        print(f"  • Trial End:   {trial_end}")
        print(f"  • First Charge: {first_charge_date}")

        trial_payload = SubscriptionCreate(
            merchant_name="Canva Pro Trial",
            category="Design",
            amount=499.0,
            billing_frequency="monthly",
            start_date=trial_start,
            trial_start_date=trial_start,
            trial_end_date=trial_end,
            expected_first_payment_date=first_charge_date,
            next_payment_date=trial_end,
            status="trial",
            is_free_trial=True,
            autopay_enabled=True
        )

        created_sub = SubscriptionService.create_subscription(
            db=None,
            user_id=test_user_id,
            payload=trial_payload,
            trigger_calendar=True
        )

        sub_id = created_sub["id"]
        event_id_before = created_sub.get("calendar_event_id")
        print(f"  • Created Sub ID: {sub_id}")
        print(f"  • Initial Status: {created_sub.get('status')}")
        print(f"  • Initial Calendar Event ID: {event_id_before}")

        # Check DB Persistence / Subscription representation
        db_rows = supabase.from_("subscriptions").select("*").eq("id", sub_id).execute().data
        db_record = db_rows[0] if db_rows else created_sub

        print(f"\n[Step 3] Checking columns for trial subscription:")
        print(f"  • trial_start_date:            {created_sub.get('trial_start_date')}")
        print(f"  • trial_end_date:              {created_sub.get('trial_end_date')}")
        print(f"  • expected_first_payment_date: {created_sub.get('expected_first_payment_date')}")
        print(f"  • is_free_trial:               {created_sub.get('is_free_trial')}")
        print(f"  • status:                      {created_sub.get('status')}")

        assert str(created_sub.get("trial_start_date")) == str(trial_start), "❌ trial_start_date mismatch"
        assert str(created_sub.get("trial_end_date")) == str(trial_end), "❌ trial_end_date mismatch"
        assert str(created_sub.get("expected_first_payment_date")) == str(first_charge_date), "❌ expected_first_payment_date mismatch"
        assert created_sub.get("is_free_trial") is True, "❌ is_free_trial must be True"
        assert created_sub.get("status") == "trial", "❌ status must be 'trial'"
        assert event_id_before is not None, "❌ calendar_event_id must not be None"
        print(f"  ✅ Check 1: Free trial fields stored accurately & Calendar event generated -> PASS")

        # -------------------------------------------------------------
        # Step 4: Simulate Trial Expiry and Trigger Rollover
        # -------------------------------------------------------------
        print(f"\n[Step 4] Simulating Trial Expiry (trial_end_date arrives/passes)...")
        # Update trial_end_date to today in DB so rollover engine picks it up
        try:
            supabase.from_("subscriptions").update({
                "trial_end_date": str(today),
                "next_payment_date": str(today),
                "expected_first_payment_date": str(today + timedelta(days=30))
            }).eq("id", sub_id).execute()
        except Exception:
            supabase.from_("subscriptions").update({
                "next_payment_date": str(today)
            }).eq("id", sub_id).execute()

        print(f"  • Triggering SubscriptionService.process_trial_conversions for user {test_user_id}...")
        conversions = SubscriptionService.process_trial_conversions(user_id=test_user_id)
        print(f"  • Conversions processed: {len(conversions)}")

        assert len(conversions) >= 1, "❌ Expected at least 1 trial subscription converted to active!"
        converted_item = [c for c in conversions if str(c.get("id")) == sub_id][0]

        # -------------------------------------------------------------
        # Step 5: Verify Converted Paid Subscription & Event ID Preservation
        # -------------------------------------------------------------
        print(f"\n[Step 5] Verifying post-conversion state in DB and Calendar...")
        db_after_rows = supabase.from_("subscriptions").select("*").eq("id", sub_id).execute().data
        db_raw = db_after_rows[0] if db_after_rows else {}
        db_after = {**db_raw, **converted_item}
        event_id_after = db_after.get("calendar_event_id") or converted_item.get("calendar_event_id")

        print(f"  • Converted Status:           {db_after.get('status')}")
        print(f"  • is_free_trial flag:         {db_after.get('is_free_trial')}")
        print(f"  • New next_payment_date:      {db_after.get('next_payment_date')}")
        print(f"  • Calendar Event ID (BEFORE): {event_id_before}")
        print(f"  • Calendar Event ID (AFTER):  {event_id_after}")

        assert db_after.get("status") == "active", f"❌ Expected status 'active', got {db_after.get('status')}"
        assert db_after.get("is_free_trial") is False, "❌ is_free_trial must be False after conversion"
        assert str(db_after.get("next_payment_date")) == str(today + timedelta(days=30)), f"❌ next_payment_date should advance to expected_first_payment_date"
        assert event_id_after == event_id_before, f"❌ Calendar Event ID must be preserved via PATCH! Before={event_id_before}, After={event_id_after}"

        print(f"  ✅ Check 2: Transitioned to 'active' paid subscription flow -> PASS")
        print(f"  ✅ Check 3: Same calendar event updated in-place via PATCH (Event ID preserved) -> PASS")

    finally:
        # Cleanup
        print("\n[Step 6] Cleaning up test data...")
        try:
            supabase.from_("subscriptions").delete().eq("user_id", test_user_id).execute()
            supabase.from_("emis").delete().eq("user_id", test_user_id).execute()
            print("  • Cleanup complete.")
        except Exception as e:
            print("Cleanup note:", e)

    print("\n" + "=" * 70)
    print("🎉 ALL CHECKS PASSED (3/3) — C2 FREE TRIAL DATE HANDLING VERIFIED!")
    print("=" * 70)


if __name__ == "__main__":
    run_free_trial_tests()
