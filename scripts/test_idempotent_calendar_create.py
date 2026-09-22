import sys
import os
import uuid
import threading
from datetime import date, timedelta

# Set up python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_supabase_client
from app.schemas.subscription import SubscriptionCreate
from app.schemas.emi import EMICreate
from app.services.subscription_service import SubscriptionService
from app.services.emi_service import EMIService
from app.services.calendar_agent_service import CalendarAgentService

def test_idempotent_creation_flow():
    print("=" * 70)
    print("🧪 AUTOMATED TEST B3: IDEMPOTENT CALENDAR EVENT CREATION")
    print("=" * 70)

    supabase = get_supabase_client()
    test_email = f"idempotent_test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"

    # Step 1: Create real test user
    auth_resp = supabase.auth.sign_up({"email": test_email, "password": test_password})
    test_user_id = str(auth_resp.user.id)
    print(f"\n[Step 1] Created test user: {test_user_id} ({test_email})")

    try:
        # -----------------------------------------------------------------
        # TEST 1: Rapid 3x Subscription Calendar Sync (Double-click simulation)
        # -----------------------------------------------------------------
        print("\n[Step 2] Creating test subscription...")
        sub_payload = SubscriptionCreate(
            merchant_name=f"Idempotent Netflix {uuid.uuid4().hex[:4]}",
            category="Entertainment",
            amount=649.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=7),
            status="active",
            autopay_enabled=True
        )
        # Create without automatic calendar trigger to manually test rapid 3x sync
        created_sub = SubscriptionService.create_subscription(None, test_user_id, sub_payload, trigger_calendar=False)
        sub_id = created_sub.get("id")
        print(f"  • Created Subscription in DB: ID = {sub_id}")

        print("\n[Step 3] Calling sync_subscription_create 3 times in rapid concurrent succession...")
        results = []
        threads = []

        def call_sub_sync():
            res = CalendarAgentService.sync_subscription_create(test_user_id, created_sub)
            results.append(res)

        for i in range(3):
            t = threading.Thread(target=call_sub_sync)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        print(f"  • Call 1 result: event_id = {results[0].get('calendar_event_id')}, status = {results[0].get('status')}")
        print(f"  • Call 2 result: event_id = {results[1].get('calendar_event_id')}, status = {results[1].get('status')}")
        print(f"  • Call 3 result: event_id = {results[2].get('calendar_event_id')}, status = {results[2].get('status')}")

        event_ids = [r.get("calendar_event_id") for r in results if r.get("calendar_event_id")]
        unique_event_ids = set(event_ids)
        print(f"\n  • Total event IDs returned: {len(event_ids)}")
        print(f"  • Unique event IDs across all 3 calls: {len(unique_event_ids)} ({unique_event_ids})")

        assert len(unique_event_ids) == 1, f"Expected exactly 1 unique event_id, got {len(unique_event_ids)}!"
        print("  ✅ Check 1: 3x rapid Subscription sync produced exactly 1 calendar event -> PASS")

        # -----------------------------------------------------------------
        # TEST 2: Rapid 3x EMI Calendar Sync (Double-click simulation)
        # -----------------------------------------------------------------
        print("\n[Step 4] Creating test EMI...")
        emi_payload = EMICreate(
            loan_name=f"Idempotent Loan {uuid.uuid4().hex[:4]}",
            total_installments=12,
            installments_paid=1,
            installment_amount=5000.0,
            next_due_date=date.today() + timedelta(days=12),
            status="active"
        )
        created_emi = EMIService.create_emi(test_user_id, emi_payload, trigger_calendar=False)
        emi_id = created_emi.get("id")
        print(f"  • Created EMI in DB: ID = {emi_id}")

        print("\n[Step 5] Calling sync_emi_create 3 times in rapid concurrent succession...")
        emi_results = []
        emi_threads = []

        def call_emi_sync():
            res = CalendarAgentService.sync_emi_create(test_user_id, created_emi)
            emi_results.append(res)

        for i in range(3):
            t = threading.Thread(target=call_emi_sync)
            emi_threads.append(t)
            t.start()

        for t in emi_threads:
            t.join()

        print(f"  • Call 1 result: event_id = {emi_results[0].get('calendar_event_id')}, status = {emi_results[0].get('status')}")
        print(f"  • Call 2 result: event_id = {emi_results[1].get('calendar_event_id')}, status = {emi_results[1].get('status')}")
        print(f"  • Call 3 result: event_id = {emi_results[2].get('calendar_event_id')}, status = {emi_results[2].get('status')}")

        emi_event_ids = [r.get("calendar_event_id") for r in emi_results if r.get("calendar_event_id")]
        unique_emi_event_ids = set(emi_event_ids)
        print(f"\n  • Total EMI event IDs returned: {len(emi_event_ids)}")
        print(f"  • Unique EMI event IDs across all 3 calls: {len(unique_emi_event_ids)} ({unique_emi_event_ids})")

        assert len(unique_emi_event_ids) == 1, f"Expected exactly 1 unique EMI event_id, got {len(unique_emi_event_ids)}!"
        print("  ✅ Check 2: 3x rapid EMI sync produced exactly 1 calendar event -> PASS")

        print("\n" + "=" * 70)
        print("🎉 ALL IDEMPOTENCY & CONCURRENCY LOCKING CHECKS PASSED")
        print("=" * 70)

    finally:
        # Cleanup
        try:
            supabase.from_("subscriptions").delete().eq("user_id", test_user_id).execute()
            supabase.from_("emis").delete().eq("user_id", test_user_id).execute()
        except Exception:
            pass

if __name__ == "__main__":
    test_idempotent_creation_flow()
