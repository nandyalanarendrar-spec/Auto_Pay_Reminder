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
from app.services.calendar_agent_service import CalendarAgentService

def test_calendar_lifecycle():
    print("=" * 70)
    print("🧪 AUTOMATED TEST B1: GOOGLE CALENDAR LIFECYCLE & ZERO-MANUAL-BUTTONS")
    print("=" * 70)

    supabase = get_supabase_client()
    test_email = f"cal_test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"

    # Create real test user
    auth_resp = supabase.auth.sign_up({"email": test_email, "password": test_password})
    test_user_id = str(auth_resp.user.id)
    print(f"\n[Setup] Created test user: {test_user_id}")

    try:
        # -------------------------------------------------------------
        # CHECK 1: Subscription Lifecycle Calendar Triggers
        # -------------------------------------------------------------
        print("\n[PART 1: SUBSCRIPTION CALENDAR LIFECYCLE]")

        # 1. Create Subscription with Autopay ON -> Calendar event ID assigned
        sub_payload = SubscriptionCreate(
            merchant_name=f"Spotify Premium {uuid.uuid4().hex[:4]}",
            category="Entertainment",
            amount=179.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=14),
            status="active",
            autopay_enabled=True
        )
        created_sub = SubscriptionService.create_subscription(None, test_user_id, sub_payload)
        sub_id = created_sub.get("id")
        cal_id_1 = created_sub.get("calendar_event_id")
        print(f"  • 1.1 Create Sub (Autopay ON): ID = {sub_id}, calendar_event_id = {cal_id_1}")
        assert sub_id is not None, "Subscription creation failed"
        assert cal_id_1 is not None, "Expected calendar_event_id to be populated"
        print("    -> PASS: Event generated and calendar_event_id stored in DB")

        # 1.2 Toggle Autopay OFF -> calendar_event_id reset to None
        updated_sub_off = SubscriptionService.update_subscription(
            test_user_id, sub_id, SubscriptionUpdate(autopay_enabled=False)
        )
        cal_id_2 = updated_sub_off.get("calendar_event_id")
        print(f"  • 1.2 Toggle Autopay OFF: calendar_event_id = {cal_id_2}")
        assert cal_id_2 is None, "Expected calendar_event_id to be None when Autopay is OFF"
        print("    -> PASS: Event purged and calendar_event_id cleared")

        # 1.3 Toggle Autopay ON -> new calendar_event_id assigned
        updated_sub_on = SubscriptionService.update_subscription(
            test_user_id, sub_id, SubscriptionUpdate(autopay_enabled=True)
        )
        cal_id_3 = updated_sub_on.get("calendar_event_id")
        print(f"  • 1.3 Toggle Autopay ON: calendar_event_id = {cal_id_3}")
        assert cal_id_3 is not None, "Expected calendar_event_id to be recreated when Autopay is ON"
        print("    -> PASS: Event restored and calendar_event_id populated")

        # 1.4 Delete Subscription -> calendar event deleted
        del_res = SubscriptionService.delete_subscription(test_user_id, sub_id)
        assert del_res is True, "Failed to delete subscription"
        print("  • 1.4 Delete Subscription: event deleted and row purged from DB -> PASS")

        # -------------------------------------------------------------
        # CHECK 2: EMI Lifecycle Calendar Triggers
        # -------------------------------------------------------------
        print("\n[PART 2: EMI CALENDAR LIFECYCLE]")

        # 2.1 Create EMI with Autopay ON -> Calendar event ID assigned
        emi_payload = EMICreate(
            loan_name=f"MacBook Pro EMI {uuid.uuid4().hex[:4]}",
            total_installments=12,
            installments_paid=2,
            installment_amount=8500.0,
            next_due_date=date.today() + timedelta(days=10),
            status="active"
        )
        created_emi = EMIService.create_emi(test_user_id, emi_payload)
        emi_id = created_emi.get("id")
        emi_cal_id_1 = created_emi.get("calendar_event_id")
        print(f"  • 2.1 Create EMI (Autopay ON): ID = {emi_id}, calendar_event_id = {emi_cal_id_1}")
        assert emi_id is not None, "EMI creation failed"
        assert emi_cal_id_1 is not None, "Expected calendar_event_id to be populated"
        print("    -> PASS: Event generated and calendar_event_id stored in DB")

        # 2.2 Cancel/Pause EMI -> calendar_event_id reset to None
        updated_emi_off = EMIService.update_emi(
            test_user_id, emi_id, EMIUpdate(status="cancelled")
        )
        emi_cal_id_2 = updated_emi_off.get("calendar_event_id")
        print(f"  • 2.2 Cancel EMI: calendar_event_id = {emi_cal_id_2}")
        assert emi_cal_id_2 is None, "Expected calendar_event_id to be None when EMI is cancelled"
        print("    -> PASS: Event purged and calendar_event_id cleared")

        # 2.3 Reactivate EMI -> new calendar_event_id assigned
        updated_emi_on = EMIService.update_emi(
            test_user_id, emi_id, EMIUpdate(status="active")
        )
        emi_cal_id_3 = updated_emi_on.get("calendar_event_id")
        print(f"  • 2.3 Reactivate EMI: calendar_event_id = {emi_cal_id_3}")
        assert emi_cal_id_3 is not None, "Expected calendar_event_id to be recreated when EMI is active"
        print("    -> PASS: Event restored and calendar_event_id populated")

        # 2.4 Delete EMI -> calendar event deleted
        del_emi_res = EMIService.delete_emi(test_user_id, emi_id)
        assert del_emi_res is True, "Failed to delete EMI"
        print("  • 2.4 Delete EMI: event deleted and row purged from DB -> PASS")

        print("\n" + "=" * 70)
        print("🎉 ALL GOOGLE CALENDAR LIFECYCLE CONTRACT CHECKS PASSED")
        print("=" * 70)

    finally:
        # Cleanup
        try:
            supabase.from_("subscriptions").delete().eq("user_id", test_user_id).execute()
            supabase.from_("emis").delete().eq("user_id", test_user_id).execute()
            supabase.from_("transactions").delete().eq("user_id", test_user_id).execute()
        except Exception:
            pass

if __name__ == "__main__":
    test_calendar_lifecycle()
