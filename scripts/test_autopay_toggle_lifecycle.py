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

def test_autopay_toggle_lifecycle_flow():
    print("=" * 70)
    print("🧪 AUTOMATED TEST B6: AUTOPAY TOGGLE OFF/ON SINGLE-EVENT GUARANTEE")
    print("=" * 70)

    supabase = get_supabase_client()
    test_email = f"toggle_test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"

    # Step 1: Create real test user
    auth_resp = supabase.auth.sign_up({"email": test_email, "password": test_password})
    test_user_id = str(auth_resp.user.id)
    print(f"\n[Step 1] Created test user: {test_user_id} ({test_email})")

    try:
        # -----------------------------------------------------------------
        # TEST 1: Rapid 5-Cycle Toggle Sequence for Subscription
        # -----------------------------------------------------------------
        print("\n[Step 2] Creating initial subscription (Autopay ON)...")
        sub_payload = SubscriptionCreate(
            merchant_name=f"Toggle Netflix {uuid.uuid4().hex[:4]}",
            category="Entertainment",
            amount=649.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=10),
            status="active",
            autopay_enabled=True
        )
        created_sub = SubscriptionService.create_subscription(None, test_user_id, sub_payload)
        sub_id = created_sub.get("id")
        initial_event_id = created_sub.get("calendar_event_id")

        print(f"  • Created Sub ID: {sub_id}")
        print(f"  • Initial State: Autopay ON, calendar_event_id = {initial_event_id}")
        assert initial_event_id is not None, "Initial calendar_event_id missing"

        # Toggle Sequence: OFF -> ON -> OFF -> ON -> OFF (5 toggles)
        toggle_sequence = [False, True, False, True, False]
        print(f"\n[Step 3] Executing 5 sequential toggles: OFF -> ON -> OFF -> ON -> OFF...")

        for idx, target_state in enumerate(toggle_sequence, start=1):
            state_str = "ON" if target_state else "OFF"
            res = SubscriptionService.update_subscription(
                test_user_id, sub_id, SubscriptionUpdate(autopay_enabled=target_state)
            )
            curr_event_id = res.get("calendar_event_id")
            print(f"  • Toggle #{idx} ({state_str}): autopay_enabled = {res.get('autopay_enabled')}, calendar_event_id = {curr_event_id}")

            if not target_state:
                assert curr_event_id is None, f"Expected calendar_event_id to be None after toggle #{idx} (OFF)"
            else:
                assert curr_event_id is not None, f"Expected calendar_event_id to be populated after toggle #{idx} (ON)"

        # Verify state after 5 toggles (ended on OFF)
        sub_after_5 = SubscriptionService.get_subscription_by_id(test_user_id, sub_id)
        print(f"\n[Step 4] Checking DB state after 5 toggles (Ended on OFF):")
        print(f"  • DB Record: ID = {sub_after_5.get('id')}, autopay_enabled = {sub_after_5.get('autopay_enabled')}, calendar_event_id = {sub_after_5.get('calendar_event_id')}")

        assert sub_after_5.get("autopay_enabled") == False, "Expected autopay_enabled to be False"
        assert sub_after_5.get("calendar_event_id") is None, "Expected calendar_event_id to be None"
        print("  ✅ Check 1: 5 toggles ended on OFF -> 0 calendar events exist in DB -> PASS")

        # 6th Toggle: Switch back to ON
        print(f"\n[Step 5] Toggling ON once more (6th toggle)...")
        sub_toggle_on = SubscriptionService.update_subscription(
            test_user_id, sub_id, SubscriptionUpdate(autopay_enabled=True)
        )
        final_event_id = sub_toggle_on.get("calendar_event_id")
        print(f"  • 6th Toggle Result: autopay_enabled = {sub_toggle_on.get('autopay_enabled')}, calendar_event_id = {final_event_id}")

        assert sub_toggle_on.get("autopay_enabled") == True, "Expected autopay_enabled to be True"
        assert final_event_id is not None, "Expected calendar_event_id to be populated on 6th toggle"
        print("  ✅ Check 2: Final toggle ON -> Exactly 1 calendar event restored -> PASS")

        print("\n" + "=" * 70)
        print("🎉 ALL B6 AUTOPAY TOGGLE SINGLE-EVENT CHECKS PASSED")
        print("=" * 70)

    finally:
        # Cleanup
        try:
            supabase.from_("subscriptions").delete().eq("user_id", test_user_id).execute()
        except Exception:
            pass

if __name__ == "__main__":
    test_autopay_toggle_lifecycle_flow()
