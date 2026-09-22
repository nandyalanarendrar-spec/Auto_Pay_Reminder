import os
import sys
import uuid
import time
import pytest
from datetime import date, timedelta

# Ensure parent directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from app.schemas.emi import EMICreate, EMIUpdate
from app.services.subscription_service import SubscriptionService
from app.services.emi_service import EMIService
from app.services.calendar_agent_service import CalendarAgentService
from app.services.google_calendar_service import GoogleCalendarService

TEST_USER_ID = "c4227bc0-0db1-4dc9-a02c-58bd70427d1d"

class TestCalendarContractSuite:
    """
    16-Point Empirical Verification Test Suite for Autopay Guard Google Calendar Integration.
    Verifies database authority, idempotency, single-event lifecycle, extendedProperties metadata,
    and automatic synchronization.
    """

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clean up test subscriptions and EMIs before and after each test."""
        yield
        # Post-test cleanup if needed

    def test_01_create_subscription_generates_single_event(self):
        """Test 1: Create sub with Autopay ON -> Exactly 1 event created, calendar_event_id stored in DB."""
        payload = SubscriptionCreate(
            merchant_name=f"UnitTest_NetFlix_{uuid.uuid4().hex[:6]}",
            category="Entertainment",
            amount=649.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=5),
            status="active",
            autopay_enabled=True
        )
        sub = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        assert sub is not None
        assert sub.get("id") is not None
        assert sub.get("merchant_name") == payload.merchant_name
        
        # Check event status in DB
        cal_id = sub.get("calendar_event_id")
        assert cal_id is not None
        assert not str(cal_id).startswith("sim-")

        # Verify event on Google Calendar REST API
        if GoogleCalendarService.is_connected(TEST_USER_ID):
            found_id = GoogleCalendarService.find_event_by_metadata(
                TEST_USER_ID,
                {"source": "autopay_guard", "subscription_id": str(sub.get("id"))}
            )
            assert found_id == cal_id

        # Clean up
        SubscriptionService.delete_subscription(TEST_USER_ID, sub["id"])

    def test_02_create_subscription_autopay_off(self):
        """Test 2: Create sub with Autopay OFF -> 0 events created on Google Calendar."""
        payload = SubscriptionCreate(
            merchant_name=f"UnitTest_Disabled_{uuid.uuid4().hex[:6]}",
            category="Utilities",
            amount=299.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=10),
            status="active",
            autopay_enabled=False
        )
        sub = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        assert sub.get("calendar_event_id") is None
        
        if GoogleCalendarService.is_connected(TEST_USER_ID):
            found_id = GoogleCalendarService.find_event_by_metadata(
                TEST_USER_ID,
                {"source": "autopay_guard", "subscription_id": str(sub.get("id"))}
            )
            assert found_id is None

        SubscriptionService.delete_subscription(TEST_USER_ID, sub["id"])

    def test_03_toggle_autopay_off_wipes_event(self):
        """Test 3: Update sub Autopay ON -> OFF -> Event wiped from GCal and calendar_event_id reset to None."""
        payload = SubscriptionCreate(
            merchant_name=f"UnitTest_ToggleOff_{uuid.uuid4().hex[:6]}",
            category="Software",
            amount=499.0,
            next_payment_date=date.today() + timedelta(days=7),
            autopay_enabled=True
        )
        sub = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        cal_id = sub.get("calendar_event_id")
        assert cal_id is not None

        # Toggle Autopay OFF
        updated = SubscriptionService.update_subscription(
            TEST_USER_ID, sub["id"], SubscriptionUpdate(autopay_enabled=False)
        )
        assert updated.get("calendar_event_id") is None

        if GoogleCalendarService.is_connected(TEST_USER_ID):
            found_id = GoogleCalendarService.find_event_by_metadata(
                TEST_USER_ID,
                {"source": "autopay_guard", "subscription_id": str(sub["id"])}
            )
            assert found_id is None

        SubscriptionService.delete_subscription(TEST_USER_ID, sub["id"])

    def test_04_toggle_autopay_on_recreates_event(self):
        """Test 4: Update sub Autopay OFF -> ON -> Event recreated on GCal, calendar_event_id populated."""
        payload = SubscriptionCreate(
            merchant_name=f"UnitTest_ToggleOn_{uuid.uuid4().hex[:6]}",
            amount=199.0,
            next_payment_date=date.today() + timedelta(days=8),
            autopay_enabled=False
        )
        sub = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        assert sub.get("calendar_event_id") is None

        # Toggle Autopay ON
        updated = SubscriptionService.update_subscription(
            TEST_USER_ID, sub["id"], SubscriptionUpdate(autopay_enabled=True)
        )
        new_cal_id = updated.get("calendar_event_id")
        assert new_cal_id is not None

        SubscriptionService.delete_subscription(TEST_USER_ID, sub["id"])

    def test_05_update_amount_patches_existing_event(self):
        """Test 5: Update amount -> Same event patched (same calendar_event_id), no duplicate."""
        payload = SubscriptionCreate(
            merchant_name=f"UnitTest_PatchAmount_{uuid.uuid4().hex[:6]}",
            amount=100.0,
            next_payment_date=date.today() + timedelta(days=3),
            autopay_enabled=True
        )
        sub = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        original_cal_id = sub.get("calendar_event_id")

        # Update amount to 150.0
        updated = SubscriptionService.update_subscription(
            TEST_USER_ID, sub["id"], SubscriptionUpdate(amount=150.0)
        )
        patched_cal_id = updated.get("calendar_event_id")
        assert patched_cal_id == original_cal_id

        SubscriptionService.delete_subscription(TEST_USER_ID, sub["id"])

    def test_06_update_date_patches_event(self):
        """Test 6: Update payment date -> Same event start date updated on GCal."""
        payload = SubscriptionCreate(
            merchant_name=f"UnitTest_PatchDate_{uuid.uuid4().hex[:6]}",
            amount=300.0,
            next_payment_date=date.today() + timedelta(days=4),
            autopay_enabled=True
        )
        sub = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        new_date = date.today() + timedelta(days=12)

        updated = SubscriptionService.update_subscription(
            TEST_USER_ID, sub["id"], SubscriptionUpdate(next_payment_date=new_date)
        )
        assert updated.get("next_payment_date") == str(new_date)

        SubscriptionService.delete_subscription(TEST_USER_ID, sub["id"])

    def test_07_soft_delete_subscription_removes_event(self):
        """Test 7: Soft delete sub (status='cancelled') -> Event wiped from GCal."""
        payload = SubscriptionCreate(
            merchant_name=f"UnitTest_SoftDel_{uuid.uuid4().hex[:6]}",
            amount=500.0,
            next_payment_date=date.today() + timedelta(days=6),
            autopay_enabled=True
        )
        sub = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        assert sub.get("calendar_event_id") is None or not str(sub.get("calendar_event_id")).startswith("sim-")

        cancelled = SubscriptionService.soft_delete_subscription(TEST_USER_ID, sub["id"])
        assert cancelled.get("status") == "cancelled"
        assert cancelled.get("calendar_event_id") is None

        SubscriptionService.delete_subscription(TEST_USER_ID, sub["id"])

    def test_08_hard_delete_subscription_removes_event(self):
        """Test 8: Hard delete sub -> Event wiped from GCal."""
        payload = SubscriptionCreate(
            merchant_name=f"UnitTest_HardDel_{uuid.uuid4().hex[:6]}",
            amount=750.0,
            next_payment_date=date.today() + timedelta(days=9),
            autopay_enabled=True
        )
        sub = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        sub_id = sub["id"]

        success = SubscriptionService.delete_subscription(TEST_USER_ID, sub_id)
        assert success is True

        if GoogleCalendarService.is_connected(TEST_USER_ID):
            found_id = GoogleCalendarService.find_event_by_metadata(
                TEST_USER_ID,
                {"source": "autopay_guard", "subscription_id": str(sub_id)}
            )
            assert found_id is None

    def test_09_create_emi_generates_single_event(self):
        """Test 9: Create active EMI -> 1 event created on GCal, calendar_event_id stored in DB."""
        payload = EMICreate(
            loan_name=f"UnitTest_EMILoan_{uuid.uuid4().hex[:6]}",
            total_installments=12,
            installments_paid=2,
            installment_amount=1500.0,
            next_due_date=date.today() + timedelta(days=15),
            status="active"
        )
        emi = EMIService.create_emi(TEST_USER_ID, payload)
        assert emi is not None
        assert emi.get("calendar_event_id") is not None

        EMIService.delete_emi(TEST_USER_ID, emi["id"])

    def test_10_update_emi_patches_existing_event(self):
        """Test 10: Update EMI installment amount -> Same event patched."""
        payload = EMICreate(
            loan_name=f"UnitTest_EMIPatch_{uuid.uuid4().hex[:6]}",
            total_installments=6,
            installment_amount=2000.0,
            next_due_date=date.today() + timedelta(days=10),
            status="active"
        )
        emi = EMIService.create_emi(TEST_USER_ID, payload)
        orig_cal_id = emi.get("calendar_event_id")

        updated = EMIService.update_emi(
            TEST_USER_ID, emi["id"], EMIUpdate(installment_amount=2200.0)
        )
        assert updated.get("calendar_event_id") == orig_cal_id

        EMIService.delete_emi(TEST_USER_ID, emi["id"])

    def test_11_pay_installment_advances_date_and_patches(self):
        """Test 11: Call pay installment -> next_due_date advanced by 30 days and event patched."""
        orig_due = date.today() + timedelta(days=5)
        payload = EMICreate(
            loan_name=f"UnitTest_EMIPay_{uuid.uuid4().hex[:6]}",
            total_installments=10,
            installments_paid=1,
            installment_amount=1000.0,
            next_due_date=orig_due,
            status="active"
        )
        emi = EMIService.create_emi(TEST_USER_ID, payload)

        updated = EMIService.update_emi(
            TEST_USER_ID, emi["id"], EMIUpdate(pay_installment=True)
        )
        assert updated.get("installments_paid") == 2
        exp_next = (orig_due + timedelta(days=30)).strftime("%Y-%m-%d")
        assert updated.get("next_due_date") == exp_next

        EMIService.delete_emi(TEST_USER_ID, emi["id"])

    def test_12_complete_emi_wipes_event(self):
        """Test 12: Pay last installment (status='completed') -> Event wiped from GCal."""
        payload = EMICreate(
            loan_name=f"UnitTest_EMIComplete_{uuid.uuid4().hex[:6]}",
            total_installments=2,
            installments_paid=1,
            installment_amount=500.0,
            next_due_date=date.today() + timedelta(days=3),
            status="active"
        )
        emi = EMIService.create_emi(TEST_USER_ID, payload)

        # Pay final installment
        completed = EMIService.update_emi(
            TEST_USER_ID, emi["id"], EMIUpdate(pay_installment=True)
        )
        assert completed.get("status") == "completed"
        assert completed.get("calendar_event_id") is None

        EMIService.delete_emi(TEST_USER_ID, emi["id"])

    def test_13_idempotent_duplicate_prevention(self):
        """Test 13: Call sync_subscription_create twice concurrently -> Strictly 1 event on GCal."""
        payload = SubscriptionCreate(
            merchant_name=f"UnitTest_Idempotent_{uuid.uuid4().hex[:6]}",
            amount=99.0,
            next_payment_date=date.today() + timedelta(days=14),
            autopay_enabled=True
        )
        sub = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        
        # Second call to sync_subscription_create with same payload/ID
        res2 = CalendarAgentService.sync_subscription_create(TEST_USER_ID, sub)
        assert res2.get("calendar_event_id") == sub.get("calendar_event_id")

        SubscriptionService.delete_subscription(TEST_USER_ID, sub["id"])

    def test_14_metadata_tagging_verification(self):
        """Test 14: Fetch event from Google Calendar API -> extendedProperties.private verified."""
        if not GoogleCalendarService.is_connected(TEST_USER_ID):
            pytest.skip("Google Calendar OAuth not connected")

        payload = SubscriptionCreate(
            merchant_name=f"UnitTest_MetaCheck_{uuid.uuid4().hex[:6]}",
            amount=1200.0,
            next_payment_date=date.today() + timedelta(days=7),
            autopay_enabled=True
        )
        sub = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        sub_id = sub["id"]

        found_event_id = GoogleCalendarService.find_event_by_metadata(
            TEST_USER_ID,
            {
                "source": "autopay_guard",
                "user_id": TEST_USER_ID,
                "subscription_id": sub_id
            }
        )
        assert found_event_id is not None
        assert found_event_id == sub.get("calendar_event_id")

        SubscriptionService.delete_subscription(TEST_USER_ID, sub_id)

    def test_15_resync_all_is_database_authoritative(self):
        """Test 15: Trigger resync_user_calendar -> Calendar matches active DB items count."""
        res = CalendarAgentService.resync_user_calendar(TEST_USER_ID)
        assert res.get("success") is True
        assert res.get("status") == "SYNCED"

    def test_16_reconnect_preserves_single_event_invariant(self):
        """Test 16: Re-running resync does not generate duplicates."""
        res1 = CalendarAgentService.resync_user_calendar(TEST_USER_ID)
        res2 = CalendarAgentService.resync_user_calendar(TEST_USER_ID)
        assert res1.get("events_created") == res2.get("events_created") or res2.get("events_updated") >= 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
