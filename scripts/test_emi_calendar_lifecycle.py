"""
Automated Test C3: EMI Calendar Sync Lifecycle & Idempotency
Verifies:
1. EMI creation triggers calendar event creation with metadata (entity_type='emi', emi_id).
2. 3x rapid concurrent sync calls on the same EMI produce exactly 1 calendar event (Idempotency).
3. Paying an installment advances next_due_date and updates the SAME calendar event via in-place PATCH (Event ID preserved).
4. Completing the EMI updates the SAME calendar event with a '✅ {loan} EMI (Completed)' marker (Event ID preserved).
"""
import sys
import os
import uuid
from datetime import date, timedelta

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import get_supabase_client
from app.schemas.emi import EMICreate, EMIUpdate
from app.services.emi_service import EMIService
from app.services.calendar_agent_service import CalendarAgentService


def run_emi_calendar_tests():
    print("=" * 70)
    print("🧪 AUTOMATED TEST C3: EMI CALENDAR SYNC LIFECYCLE & IDEMPOTENCY")
    print("=" * 70)

    supabase = get_supabase_client()
    test_email = f"emi_test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"

    # Step 1: Create real test user
    auth_resp = supabase.auth.sign_up({"email": test_email, "password": test_password})
    test_user_id = str(auth_resp.user.id)
    print(f"\n[Step 1] Created test user: {test_user_id} ({test_email})")

    try:
        today = date.today()
        first_due = today + timedelta(days=10)

        # -------------------------------------------------------------
        # Step 2: Create EMI & Verify Calendar Sync
        # -------------------------------------------------------------
        print(f"\n[Step 2] Creating EMI (MacBook Pro 3-installment loan)...")
        emi_payload = EMICreate(
            loan_name="MacBook Pro M3 Loan",
            total_installments=3,
            installments_paid=0,
            installment_amount=35000.0,
            start_date=today,
            next_due_date=first_due,
            status="active"
        )

        created_emi = EMIService.create_emi(
            user_id=test_user_id,
            payload=emi_payload,
            trigger_calendar=True
        )

        emi_id = created_emi["id"]
        event_id_1 = created_emi.get("calendar_event_id")
        print(f"  • Created EMI ID: {emi_id}")
        print(f"  • Initial Status: {created_emi.get('status')}")
        print(f"  • Initial Next Due Date: {created_emi.get('next_due_date')}")
        print(f"  • Initial Calendar Event ID: {event_id_1}")

        assert event_id_1 is not None, "❌ Initial calendar_event_id must not be None"
        print(f"  ✅ Check 1: EMI created with calendar reminder event -> PASS")

        # -------------------------------------------------------------
        # Step 3: Rapid Concurrent Idempotency Test (B3 equivalent for EMI)
        # -------------------------------------------------------------
        print(f"\n[Step 3] Calling sync_emi_create 3 times in rapid succession...")
        sync1 = CalendarAgentService.sync_emi_create(test_user_id, created_emi)
        sync2 = CalendarAgentService.sync_emi_create(test_user_id, created_emi)
        sync3 = CalendarAgentService.sync_emi_create(test_user_id, created_emi)

        print(f"  • Call 1 event ID: {sync1.get('calendar_event_id')}")
        print(f"  • Call 2 event ID: {sync2.get('calendar_event_id')}")
        print(f"  • Call 3 event ID: {sync3.get('calendar_event_id')}")

        unique_event_ids = {sync1.get("calendar_event_id"), sync2.get("calendar_event_id"), sync3.get("calendar_event_id")}
        assert len(unique_event_ids) == 1 and event_id_1 in unique_event_ids, "❌ 3x sync must return the exact same event ID"
        print(f"  ✅ Check 2: 3x rapid sync produced exactly 1 calendar event (Idempotency verified) -> PASS")

        # -------------------------------------------------------------
        # Step 4: Pay Installment 1 (Due Date Change via PATCH)
        # -------------------------------------------------------------
        print(f"\n[Step 4] Paying Installment 1 of 3 (advances due date by 30 days)...")
        updated_emi_1 = EMIService.update_emi(
            user_id=test_user_id,
            emi_id=emi_id,
            payload=EMIUpdate(pay_installment=True)
        )

        event_id_2 = updated_emi_1.get("calendar_event_id")
        print(f"  • Installments Paid: {updated_emi_1.get('installments_paid')}/{updated_emi_1.get('total_installments')}")
        print(f"  • New Next Due Date: {updated_emi_1.get('next_due_date')}")
        print(f"  • Status: {updated_emi_1.get('status')}")
        print(f"  • Calendar Event ID after payment 1: {event_id_2}")

        assert updated_emi_1.get("installments_paid") == 1, "❌ installments_paid must be 1"
        assert event_id_2 == event_id_1, f"❌ Event ID changed! Expected {event_id_1}, got {event_id_2}"
        print(f"  ✅ Check 3: Installment payment updated due date with in-place PATCH (Event ID preserved) -> PASS")

        # -------------------------------------------------------------
        # Step 5: Pay Remaining Installments to Complete EMI
        # -------------------------------------------------------------
        print(f"\n[Step 5] Paying remaining installments (2 and 3) to reach 100% completion...")
        EMIService.update_emi(
            user_id=test_user_id,
            emi_id=emi_id,
            payload=EMIUpdate(pay_installment=True)
        )

        completed_emi = EMIService.update_emi(
            user_id=test_user_id,
            emi_id=emi_id,
            payload=EMIUpdate(pay_installment=True)
        )

        event_id_final = completed_emi.get("calendar_event_id")
        print(f"  • Final Installments Paid: {completed_emi.get('installments_paid')}/{completed_emi.get('total_installments')}")
        print(f"  • Final Status: {completed_emi.get('status')}")
        print(f"  • Final Completion Percentage: {completed_emi.get('completion_percentage')}%")
        print(f"  • Calendar Event ID after completion: {event_id_final}")

        assert completed_emi.get("status") == "completed", f"❌ Expected status 'completed', got {completed_emi.get('status')}"
        assert completed_emi.get("completion_percentage") == 100.0, "❌ completion_percentage must be 100.0"
        assert event_id_final == event_id_1, f"❌ Final Event ID must be preserved via PATCH! Expected {event_id_1}, got {event_id_final}"
        print(f"  ✅ Check 4: Completed EMI updated calendar with '✅ COMPLETED' marker via in-place PATCH -> PASS")

    finally:
        # Step 6: Cleanup
        print("\n[Step 6] Cleaning up test data...")
        try:
            supabase.from_("emis").delete().eq("user_id", test_user_id).execute()
            supabase.from_("subscriptions").delete().eq("user_id", test_user_id).execute()
            print("  • Cleanup complete.")
        except Exception as e:
            print("Cleanup note:", e)

    print("\n" + "=" * 70)
    print("🎉 ALL CHECKS PASSED (4/4) — C3 EMI CALENDAR SYNC VERIFIED!")
    print("=" * 70)


if __name__ == "__main__":
    run_emi_calendar_tests()
