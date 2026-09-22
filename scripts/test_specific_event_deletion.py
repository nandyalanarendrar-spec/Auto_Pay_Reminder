import sys
import os
import uuid
from datetime import date, timedelta

# Set up python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_supabase_client
from app.schemas.subscription import SubscriptionCreate
from app.schemas.emi import EMICreate
from app.services.subscription_service import SubscriptionService
from app.services.emi_service import EMIService

def test_specific_event_deletion_flow():
    print("=" * 70)
    print("🧪 AUTOMATED TEST B5: DELETE ONLY SPECIFIC EVENT ID (SAME MERCHANT EDGE CASE)")
    print("=" * 70)

    supabase = get_supabase_client()
    test_email = f"delete_iso_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"

    # Step 1: Create real test user
    auth_resp = supabase.auth.sign_up({"email": test_email, "password": test_password})
    test_user_id = str(auth_resp.user.id)
    print(f"\n[Step 1] Created test user: {test_user_id} ({test_email})")

    try:
        # -----------------------------------------------------------------
        # TEST 1: Two Subscriptions with Identical Merchant Name
        # -----------------------------------------------------------------
        shared_merchant = "Netflix Premium India"
        print(f"\n[Step 2] Creating 2 separate subscriptions with identical merchant name: '{shared_merchant}'...")

        # Sub 1 (Personal Account)
        sub1_payload = SubscriptionCreate(
            merchant_name=shared_merchant,
            category="Entertainment",
            amount=199.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=5),
            status="active",
            autopay_enabled=True
        )
        sub1 = SubscriptionService.create_subscription(None, test_user_id, sub1_payload)
        sub1_id = sub1.get("id")
        sub1_cal_id = sub1.get("calendar_event_id")

        # Sub 2 (Family Account)
        sub2_payload = SubscriptionCreate(
            merchant_name=shared_merchant,
            category="Entertainment",
            amount=649.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=20),
            status="active",
            autopay_enabled=True
        )
        sub2 = SubscriptionService.create_subscription(None, test_user_id, sub2_payload)
        sub2_id = sub2.get("id")
        sub2_cal_id = sub2.get("calendar_event_id")

        print(f"  • Sub 1 (Plan 1): ID = {sub1_id}, Amount = ₹199, Event ID = {sub1_cal_id}")
        print(f"  • Sub 2 (Plan 2): ID = {sub2_id}, Amount = ₹649, Event ID = {sub2_cal_id}")
        assert sub1_id != sub2_id, "Subscription IDs must be distinct"
        assert sub1_cal_id != sub2_cal_id, "Calendar event IDs must be distinct"

        print(f"\n[Step 3] Deleting ONLY Sub 1 (ID: {sub1_id})...")
        del_sub1 = SubscriptionService.delete_subscription(test_user_id, sub1_id)
        assert del_sub1 is True, "Failed to delete Sub 1"

        print(f"\n[Step 4] Verifying Sub 1 is gone and Sub 2 remains completely intact...")
        sub1_check = SubscriptionService.get_subscription_by_id(test_user_id, sub1_id)
        sub2_check = SubscriptionService.get_subscription_by_id(test_user_id, sub2_id)

        print(f"  • Sub 1 lookup result: {sub1_check} (Deleted as expected)")
        print(f"  • Sub 2 lookup result: Found ID = {sub2_check.get('id')}, Amount = ₹{sub2_check.get('amount')}, Event ID = {sub2_check.get('calendar_event_id')}")

        assert sub1_check is None, "Sub 1 still exists in DB!"
        assert sub2_check is not None, "COLLATERAL DAMAGE: Sub 2 was accidentally deleted by merchant name!"
        assert sub2_check.get("calendar_event_id") == sub2_cal_id, "Sub 2 calendar event ID was altered or cleared!"
        print(f"  ✅ Check 1: Deleted Sub 1 without affecting Sub 2 (same merchant name '{shared_merchant}') -> PASS")

        # -----------------------------------------------------------------
        # TEST 2: Two EMIs with Identical Loan/Lender Name
        # -----------------------------------------------------------------
        shared_lender = "HDFC Personal Loan"
        print(f"\n[Step 5] Creating 2 separate EMIs with identical lender name: '{shared_lender}'...")

        emi1_payload = EMICreate(
            loan_name=shared_lender,
            total_installments=12,
            installments_paid=2,
            installment_amount=4500.0,
            next_due_date=date.today() + timedelta(days=8),
            status="active"
        )
        emi1 = EMIService.create_emi(test_user_id, em1_payload := emi1_payload)
        emi1_id = emi1.get("id")
        emi1_cal_id = emi1.get("calendar_event_id")

        emi2_payload = EMICreate(
            loan_name=shared_lender,
            total_installments=24,
            installments_paid=6,
            installment_amount=9500.0,
            next_due_date=date.today() + timedelta(days=18),
            status="active"
        )
        emi2 = EMIService.create_emi(test_user_id, emi2_payload)
        emi2_id = emi2.get("id")
        emi2_cal_id = emi2.get("calendar_event_id")

        print(f"  • EMI 1: ID = {emi1_id}, Amount = ₹4,500, Event ID = {emi1_cal_id}")
        print(f"  • EMI 2: ID = {emi2_id}, Amount = ₹9,500, Event ID = {emi2_cal_id}")
        assert emi1_id != emi2_id
        assert emi1_cal_id != emi2_cal_id

        print(f"\n[Step 6] Deleting ONLY EMI 1 (ID: {emi1_id})...")
        del_emi1 = EMIService.delete_emi(test_user_id, emi1_id)
        assert del_emi1 is True, "Failed to delete EMI 1"

        print(f"\n[Step 7] Verifying EMI 1 is gone and EMI 2 remains completely intact...")
        emi1_check = EMIService.get_emi_by_id(test_user_id, emi1_id)
        emi2_check = EMIService.get_emi_by_id(test_user_id, emi2_id)

        print(f"  • EMI 1 lookup result: {emi1_check} (Deleted as expected)")
        print(f"  • EMI 2 lookup result: Found ID = {emi2_check.get('id') if emi2_check else None}, Amount = ₹{emi2_check.get('installment_amount') if emi2_check else None}, Event ID = {emi2_check.get('calendar_event_id') if emi2_check else None}")

        assert emi1_check is None, "EMI 1 still exists in DB!"
        assert emi2_check is not None, "COLLATERAL DAMAGE: EMI 2 was accidentally deleted by lender name!"
        assert emi2_check.get("calendar_event_id") == emi2_cal_id, "EMI 2 calendar event ID was altered or cleared!"
        print(f"  ✅ Check 2: Deleted EMI 1 without affecting EMI 2 (same lender name '{shared_lender}') -> PASS")

        print("\n" + "=" * 70)
        print("🎉 ALL B5 SPECIFIC EVENT DELETION & ISOLATION CHECKS PASSED")
        print("=" * 70)

    finally:
        # Cleanup
        try:
            supabase.from_("subscriptions").delete().eq("user_id", test_user_id).execute()
            supabase.from_("emis").delete().eq("user_id", test_user_id).execute()
        except Exception:
            pass

if __name__ == "__main__":
    test_specific_event_deletion_flow()
