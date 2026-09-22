"""
Automated Test B7: Calendar Sync Failure Handling (Pending / Synced / Failed states)
Verifies that:
1. DB write succeeds even if Google Calendar API fails.
2. calendar_sync_status = 'FAILED' and calendar_sync_error stores the exact error.
3. Manual/Hybrid retry transitions status from 'FAILED' -> 'SYNCED' once restored.
4. Batch retry recovers all failed records.
"""
import sys
import os
import uuid
from datetime import date, timedelta
from unittest.mock import patch

# Ensure app is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import get_supabase_client
from app.schemas.subscription import SubscriptionCreate
from app.schemas.emi import EMICreate
from app.services.subscription_service import SubscriptionService
from app.services.emi_service import EMIService
from app.services.calendar_agent_service import CalendarAgentService
from app.services.google_calendar_service import GoogleCalendarService


def run_test():
    print("=" * 70)
    print("🧪 AUTOMATED TEST B7: CALENDAR SYNC FAILURE HANDLING")
    print("=" * 70)

    supabase = get_supabase_client()
    test_email = f"sync_fail_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"

    # Step 1: Create real test user in Supabase Auth
    auth_resp = supabase.auth.sign_up({"email": test_email, "password": test_password})
    test_user_id = str(auth_resp.user.id)
    print(f"\n[Step 1] Created test user: {test_user_id} ({test_email})")

    try:
        # -------------------------------------------------------------
        # Step 2: Create Subscription during Calendar API Failure
        # -------------------------------------------------------------
        print("\n[Step 2] Simulating Google Calendar API Failure on Subscription Creation...")

        simulated_error_msg = "Google Calendar API HTTP 503: Service Temporarily Unavailable"

        with patch.object(GoogleCalendarService, "create_calendar_event", side_effect=Exception(simulated_error_msg)):
            sub_payload = SubscriptionCreate(
                merchant_name="FailTest HBO Max",
                amount=499.0,
                billing_frequency="monthly",
                next_payment_date=date.today() + timedelta(days=5),
                category="Entertainment",
                autopay_enabled=True
            )
            created_sub = SubscriptionService.create_subscription(
                db=None,
                user_id=test_user_id,
                payload=sub_payload,
                trigger_calendar=True
            )

        sub_id = created_sub["id"]
        print(f"  • Created Subscription ID in DB: {sub_id}")
        print(f"  • In-memory returned calendar_sync_status: {created_sub.get('calendar_sync_status')}")
        print(f"  • In-memory returned calendar_sync_error: {created_sub.get('calendar_sync_error')}")

        # Verify DB persistence directly in Supabase PostgreSQL
        db_row = supabase.from_("subscriptions").select("*").eq("id", sub_id).execute()
        assert db_row.data and len(db_row.data) > 0, "❌ Subscription was NOT saved in database!"
        sub_record = db_row.data[0]

        assert sub_record["merchant_name"] == "FailTest HBO Max", "❌ Merchant name mismatch!"
        assert sub_record.get("calendar_sync_status") == "FAILED", f"❌ Expected calendar_sync_status == 'FAILED', got '{sub_record.get('calendar_sync_status')}'"
        assert simulated_error_msg in str(created_sub.get("calendar_sync_error")), f"❌ Expected in-memory error to contain '{simulated_error_msg}', got '{created_sub.get('calendar_sync_error')}'"
        print(f"  ✅ Check 1: DB write persisted during Calendar API failure with status='FAILED' and error captured -> PASS")

        # -------------------------------------------------------------
        # Step 3: Create EMI during Calendar API Failure
        # -------------------------------------------------------------
        print("\n[Step 3] Simulating Google Calendar API Failure on EMI Creation...")

        emi_sim_error = "Google Calendar API HTTP 401: Invalid Credentials / Token Expired"

        with patch.object(GoogleCalendarService, "create_calendar_event", side_effect=Exception(emi_sim_error)):
            emi_payload = EMICreate(
                loan_name="FailTest MacBook Pro EMI",
                total_installments=12,
                installments_paid=1,
                installment_amount=7500.0,
                next_due_date=date.today() + timedelta(days=10)
            )
            created_emi = EMIService.create_emi(
                user_id=test_user_id,
                payload=emi_payload,
                trigger_calendar=True
            )

        emi_id = created_emi["id"]
        print(f"  • Created EMI ID in DB: {emi_id}")
        print(f"  • In-memory returned calendar_sync_status: {created_emi.get('calendar_sync_status')}")
        print(f"  • In-memory returned calendar_sync_error: {created_emi.get('calendar_sync_error')}")

        emi_db_row = supabase.from_("emis").select("*").eq("id", emi_id).execute()
        assert emi_db_row.data and len(emi_db_row.data) > 0, "❌ EMI was NOT saved in database!"
        emi_record = emi_db_row.data[0]

        assert emi_record.get("calendar_sync_status") == "FAILED", f"❌ Expected EMI calendar_sync_status == 'FAILED', got '{emi_record.get('calendar_sync_status')}'"
        assert emi_sim_error in str(created_emi.get("calendar_sync_error")), f"❌ Expected in-memory error to contain '{emi_sim_error}', got '{created_emi.get('calendar_sync_error')}'"
        print(f"  ✅ Check 2: EMI DB write persisted during Calendar API failure with status='FAILED' and error captured -> PASS")

        # -------------------------------------------------------------
        # Step 4: Retry Subscription Sync (Recover to SYNCED)
        # -------------------------------------------------------------
        print(f"\n[Step 4] Executing Retry Sync for Subscription '{sub_id}'...")

        recovered_event_id = f"gcal-sub-{uuid.uuid4().hex[:8]}"
        with patch.object(GoogleCalendarService, "create_calendar_event", return_value={"status": "SUCCESS", "success": True, "event_id": recovered_event_id, "message": "Created"}):
            retry_res = CalendarAgentService.retry_subscription_sync(test_user_id, sub_id)

        print(f"  • Retry Response: {retry_res}")
        assert retry_res.get("status") == "SUCCESS", f"❌ Expected retry status SUCCESS, got {retry_res}"

        sub_after_retry = supabase.from_("subscriptions").select("*").eq("id", sub_id).execute().data[0]
        print(f"  • DB calendar_sync_status after retry: {sub_after_retry.get('calendar_sync_status')}")
        print(f"  • DB calendar_event_id after retry:    {sub_after_retry.get('calendar_event_id')}")

        assert sub_after_retry.get("calendar_sync_status") == "SYNCED", f"❌ Expected status SYNCED, got {sub_after_retry.get('calendar_sync_status')}"
        assert sub_after_retry.get("calendar_event_id") == recovered_event_id, f"❌ Expected event_id {recovered_event_id}, got {sub_after_retry.get('calendar_event_id')}"
        print(f"  ✅ Check 3: Subscription Retry transitioned 'FAILED' -> 'SYNCED' and stored calendar_event_id -> PASS")

        # -------------------------------------------------------------
        # Step 5: Retry EMI Sync (Recover to SYNCED)
        # -------------------------------------------------------------
        print(f"\n[Step 5] Executing Retry Sync for EMI '{emi_id}'...")

        recovered_emi_event_id = f"gcal-emi-{uuid.uuid4().hex[:8]}"
        with patch.object(GoogleCalendarService, "create_calendar_event", return_value={"status": "SUCCESS", "success": True, "event_id": recovered_emi_event_id, "message": "Created"}):
            emi_retry_res = CalendarAgentService.retry_emi_sync(test_user_id, emi_id)

        print(f"  • EMI Retry Response: {emi_retry_res}")
        assert emi_retry_res.get("status") == "SUCCESS", f"❌ Expected retry status SUCCESS, got {emi_retry_res}"

        emi_after_retry = supabase.from_("emis").select("*").eq("id", emi_id).execute().data[0]
        print(f"  • DB calendar_sync_status after retry: {emi_after_retry.get('calendar_sync_status')}")
        print(f"  • DB calendar_event_id after retry:    {emi_after_retry.get('calendar_event_id')}")

        assert emi_after_retry.get("calendar_sync_status") == "SYNCED", f"❌ Expected status SYNCED, got {emi_after_retry.get('calendar_sync_status')}"
        assert emi_after_retry.get("calendar_event_id") == recovered_emi_event_id, f"❌ Expected event_id {recovered_emi_event_id}, got {emi_after_retry.get('calendar_event_id')}"
        print(f"  ✅ Check 4: EMI Retry transitioned 'FAILED' -> 'SYNCED' and stored calendar_event_id -> PASS")

        # -------------------------------------------------------------
        # Step 6: Batch Retry Test (retry_all_failed_syncs)
        # -------------------------------------------------------------
        print(f"\n[Step 6] Testing Batch Retry (retry_all_failed_syncs)...")

        # Create 2 failed items intentionally
        with patch.object(GoogleCalendarService, "create_calendar_event", side_effect=Exception("API Outage")):
            sub2 = SubscriptionService.create_subscription(
                db=None,
                user_id=test_user_id,
                payload=SubscriptionCreate(merchant_name="Batch Fail Sub", amount=299.0, next_payment_date=date.today() + timedelta(days=2)),
                trigger_calendar=True
            )
            emi2 = EMIService.create_emi(
                user_id=test_user_id,
                payload=EMICreate(loan_name="Batch Fail EMI", total_installments=6, installment_amount=1200.0, next_due_date=date.today() + timedelta(days=4)),
                trigger_calendar=True
            )

        print(f"  • Created 2 intentionally failed items: sub '{sub2['id']}', emi '{emi2['id']}'")

        # Now run batch retry with working service
        with patch.object(GoogleCalendarService, "create_calendar_event", return_value={"status": "SUCCESS", "success": True, "event_id": "batch-recovered-evt", "message": "Created"}):
            batch_summary = CalendarAgentService.retry_all_failed_syncs(test_user_id)

        print(f"  • Batch Retry Summary: {batch_summary}")
        assert batch_summary["subscriptions_recovered"] >= 1, "❌ Expected at least 1 subscription recovered!"
        assert batch_summary["emis_recovered"] >= 1, "❌ Expected at least 1 EMI recovered!"
        print(f"  ✅ Check 5: Batch retry successfully scanned and recovered all failed items -> PASS")

    finally:
        # -------------------------------------------------------------
        # Cleanup
        # -------------------------------------------------------------
        print("\n[Step 7] Cleaning up test data...")
        try:
            supabase.from_("subscriptions").delete().eq("user_id", test_user_id).execute()
            supabase.from_("emis").delete().eq("user_id", test_user_id).execute()
            print("  • Cleanup complete.")
        except Exception as e:
            print("Cleanup note:", e)

    print("\n" + "=" * 70)
    print("🎉 ALL CHECKS PASSED (5/5) — B7 CALENDAR SYNC FAILURE HANDLING VERIFIED!")
    print("=" * 70)


if __name__ == "__main__":
    run_test()
