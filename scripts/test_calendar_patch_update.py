import sys
import os
import uuid
from datetime import date, timedelta

# Set up python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_supabase_client
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from app.schemas.emi import EMICreate, EMIUpdate
from app.services.subscription_service import SubscriptionService
from app.services.emi_service import EMIService

def test_calendar_patch_update_flow():
    print("=" * 70)
    print("🧪 AUTOMATED TEST B4: EDIT SUBSCRIPTION/EMI -> UPDATE SAME EVENT (PATCH)")
    print("=" * 70)

    supabase = get_supabase_client()
    test_email = f"patch_test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"

    # Step 1: Create real test user
    auth_resp = supabase.auth.sign_up({"email": test_email, "password": test_password})
    test_user_id = str(auth_resp.user.id)
    print(f"\n[Step 1] Created test user: {test_user_id} ({test_email})")

    try:
        # -----------------------------------------------------------------
        # TEST 1: Subscription Edit Date -> Same Event ID Patched
        # -----------------------------------------------------------------
        initial_date = date(2026, 9, 20)
        updated_date = date(2026, 9, 25)

        print(f"\n[Step 2] Creating subscription with initial renewal date: {initial_date}...")
        sub_payload = SubscriptionCreate(
            merchant_name=f"Netflix Patch Test {uuid.uuid4().hex[:4]}",
            category="Entertainment",
            amount=649.0,
            billing_frequency="monthly",
            next_payment_date=initial_date,
            status="active",
            autopay_enabled=True
        )
        created_sub = SubscriptionService.create_subscription(None, test_user_id, sub_payload)
        sub_id = created_sub.get("id")
        event_id_before = created_sub.get("calendar_event_id")

        print(f"  • Created Sub ID: {sub_id}")
        print(f"  • Initial Date: {created_sub.get('next_payment_date')}")
        print(f"  • Calendar Event ID (BEFORE edit): {event_id_before}")
        assert event_id_before is not None, "Failed to create initial calendar event"

        print(f"\n[Step 3] Editing subscription renewal date to {updated_date}...")
        updated_sub = SubscriptionService.update_subscription(
            test_user_id, sub_id, SubscriptionUpdate(next_payment_date=updated_date)
        )
        event_id_after = updated_sub.get("calendar_event_id")

        print(f"  • Updated Date in DB: {updated_sub.get('next_payment_date')}")
        print(f"  • Calendar Event ID (AFTER edit):  {event_id_after}")

        # Verification
        assert str(updated_sub.get("next_payment_date"))[:10] == str(updated_date), "Date failed to update in DB"
        assert event_id_after == event_id_before, f"EVENT ID CHANGED! Before: {event_id_before}, After: {event_id_after}"
        print(f"  ✅ Check 1: Subscription updated via PATCH — Event ID remained identical ({event_id_before}) -> PASS")

        # -----------------------------------------------------------------
        # TEST 2: EMI Edit Due Date -> Same Event ID Patched
        # -----------------------------------------------------------------
        emi_initial_date = date(2026, 10, 10)
        emi_updated_date = date(2026, 10, 15)

        print(f"\n[Step 4] Creating EMI with initial due date: {emi_initial_date}...")
        emi_payload = EMICreate(
            loan_name=f"HDFC Auto Loan {uuid.uuid4().hex[:4]}",
            total_installments=24,
            installments_paid=4,
            installment_amount=12000.0,
            next_due_date=emi_initial_date,
            status="active"
        )
        created_emi = EMIService.create_emi(test_user_id, emi_payload)
        emi_id = created_emi.get("id")
        emi_event_id_before = created_emi.get("calendar_event_id")

        print(f"  • Created EMI ID: {emi_id}")
        print(f"  • Initial Due Date: {created_emi.get('next_due_date')}")
        print(f"  • Calendar Event ID (BEFORE edit): {emi_event_id_before}")
        assert emi_event_id_before is not None, "Failed to create initial EMI calendar event"

        print(f"\n[Step 5] Editing EMI due date to {emi_updated_date}...")
        updated_emi = EMIService.update_emi(
            test_user_id, emi_id, EMIUpdate(next_due_date=emi_updated_date)
        )
        emi_event_id_after = updated_emi.get("calendar_event_id")

        print(f"  • Updated Due Date in DB: {updated_emi.get('next_due_date')}")
        print(f"  • Calendar Event ID (AFTER edit):  {emi_event_id_after}")

        # Verification
        assert str(updated_emi.get("next_due_date"))[:10] == str(emi_updated_date), "EMI Due Date failed to update in DB"
        assert emi_event_id_after == emi_event_id_before, f"EMI EVENT ID CHANGED! Before: {emi_event_id_before}, After: {emi_event_id_after}"
        print(f"  ✅ Check 2: EMI updated via PATCH — Event ID remained identical ({emi_event_id_before}) -> PASS")

        print("\n" + "=" * 70)
        print("🎉 ALL B4 PATCH UPDATE EVENT ID PRESERVATION CHECKS PASSED")
        print("=" * 70)

    finally:
        # Cleanup
        try:
            supabase.from_("subscriptions").delete().eq("user_id", test_user_id).execute()
            supabase.from_("emis").delete().eq("user_id", test_user_id).execute()
        except Exception:
            pass

if __name__ == "__main__":
    test_calendar_patch_update_flow()
