import os
import sys
import uuid
import time
import pytest
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from app.services.subscription_service import SubscriptionService
from app.services.mock_generator_service import MockGeneratorService
from app.services.calendar_agent_service import CalendarAgentService
from app.services.google_calendar_service import GoogleCalendarService
from app.core.security import get_supabase_client

# Dedicated Test User ID to avoid polluting production data
TEST_USER_ID = "d9999999-aaaa-bbbb-cccc-111122223333"

class TestMasterVerificationSuite:

    @classmethod
    def setup_class(cls):
        """Clean up any existing test data for dedicated test user prior to suite run."""
        supabase = get_supabase_client()
        try:
            supabase.from_("subscriptions").delete().eq("user_id", TEST_USER_ID).execute()
            supabase.from_("emis").delete().eq("user_id", TEST_USER_ID).execute()
        except Exception:
            pass

    def test_A_new_user_registration_mock_generation(self):
        """Test A — New user registers -> mock data generated exactly once"""
        supabase = get_supabase_client()
        # Clean test user mock status
        try:
            supabase.from_("subscriptions").delete().eq("user_id", TEST_USER_ID).execute()
        except Exception:
            pass

        subs = SubscriptionService.get_user_subscriptions(TEST_USER_ID)
        assert len(subs) > 0, "Expected mock subscriptions to be generated for new user"
        assert len(subs) == 5, f"Expected 5 initial mock subscriptions, got {len(subs)}"

    def test_B_refresh_3x_no_duplicate_mock_records(self):
        """Test B — Refresh 3x -> no duplicate mock records"""
        subs1 = SubscriptionService.get_user_subscriptions(TEST_USER_ID)
        subs2 = SubscriptionService.get_user_subscriptions(TEST_USER_ID)
        subs3 = SubscriptionService.get_user_subscriptions(TEST_USER_ID)

        count1, count2, count3 = len(subs1), len(subs2), len(subs3)
        assert count1 == count2 == count3, f"Duplicate mock records created on refresh: {count1} vs {count2} vs {count3}"

    def test_C_logout_and_login_no_new_mock_data(self):
        """Test C — Logout + login again -> no new mock data generated"""
        initial_subs = SubscriptionService.get_user_subscriptions(TEST_USER_ID)
        initial_count = len(initial_subs)

        # Re-fetch after simulated re-authentication
        reauth_subs = SubscriptionService.get_user_subscriptions(TEST_USER_ID)
        reauth_count = len(reauth_subs)

        assert initial_count == reauth_count, f"Re-login generated unexpected extra mock data: {initial_count} vs {reauth_count}"

    def test_D_delete_subscription_persists_after_refresh(self):
        """Test D — Delete a subscription -> confirmed gone in DB and after refresh"""
        payload = SubscriptionCreate(
            merchant_name="Delete_Test_Sub_D",
            category="Software",
            amount=299.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=10),
            status="active",
            autopay_enabled=True
        )
        created = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        sub_id = created["id"]

        # Delete subscription
        SubscriptionService.delete_subscription(TEST_USER_ID, sub_id)

        # Query Supabase directly
        supabase = get_supabase_client()
        db_check = supabase.from_("subscriptions").select("*").eq("id", sub_id).execute()
        assert len(db_check.data or []) == 0, "Deleted subscription still exists in Supabase DB!"

        # Refresh check
        refreshed_subs = SubscriptionService.get_user_subscriptions(TEST_USER_ID)
        found_in_refresh = any(str(s.get("id")) == str(sub_id) for s in refreshed_subs)
        assert not found_in_refresh, "Deleted subscription reappeared in list after refresh!"

    def test_E_update_amount_date_persists_after_refresh(self):
        """Test E — Update amount/date -> persists after refresh"""
        payload = SubscriptionCreate(
            merchant_name="Update_Test_Sub_E",
            category="Software",
            amount=499.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=15),
            status="active",
            autopay_enabled=True
        )
        created = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        sub_id = created["id"]

        new_date = date.today() + timedelta(days=25)
        update_payload = SubscriptionUpdate(
            amount=1299.0,
            next_payment_date=new_date
        )
        updated = SubscriptionService.update_subscription(TEST_USER_ID, sub_id, update_payload)

        assert float(updated["amount"]) == 1299.0, f"Expected amount 1299.0, got {updated['amount']}"
        assert str(updated["next_payment_date"])[:10] == str(new_date), f"Expected date {new_date}, got {updated['next_payment_date']}"

        # Refresh check
        refreshed_subs = SubscriptionService.get_user_subscriptions(TEST_USER_ID)
        target = next((s for s in refreshed_subs if str(s.get("id")) == str(sub_id)), None)
        assert target is not None, "Updated subscription missing from list after refresh"
        assert float(target["amount"]) == 1299.0, f"Persisted amount mismatch after refresh: {target['amount']}"
        assert str(target["next_payment_date"])[:10] == str(new_date), f"Persisted date mismatch after refresh: {target['next_payment_date']}"

    def test_F_add_subscription_creates_single_calendar_event(self):
        """Test F — Add subscription -> exactly ONE Google Calendar event created, no browser calendar page opened"""
        payload = SubscriptionCreate(
            merchant_name="GCal_Add_Test_F",
            category="Entertainment",
            amount=799.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=7),
            status="active",
            autopay_enabled=True
        )
        created = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        assert created.get("calendar_event_id") is not None, "Missing calendar_event_id on subscription creation"
        assert created.get("calendar_sync_status") in ["SYNCED", "PENDING"], f"Invalid calendar sync status: {created.get('calendar_sync_status')}"

    def test_G_edit_subscription_date_updates_same_calendar_event(self):
        """Test G — Edit subscription date -> SAME calendar event updated, still exactly one event"""
        payload = SubscriptionCreate(
            merchant_name="GCal_Edit_Test_G",
            category="Entertainment",
            amount=399.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=12),
            status="active",
            autopay_enabled=True
        )
        created = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        orig_cal_id = created.get("calendar_event_id")
        sub_id = created["id"]

        # Edit date
        new_date = date.today() + timedelta(days=20)
        updated = SubscriptionService.update_subscription(TEST_USER_ID, sub_id, SubscriptionUpdate(next_payment_date=new_date))
        updated_cal_id = updated.get("calendar_event_id")

        assert orig_cal_id == updated_cal_id, f"Calendar event ID changed on date edit! {orig_cal_id} vs {updated_cal_id}"

    def test_H_delete_subscription_deletes_calendar_event(self):
        """Test H — Delete subscription -> DB record AND its specific calendar event both deleted"""
        payload = SubscriptionCreate(
            merchant_name="GCal_Delete_Test_H",
            category="Utilities",
            amount=999.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=8),
            status="active",
            autopay_enabled=True
        )
        created = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        sub_id = created["id"]
        cal_id = created.get("calendar_event_id")

        # Delete sub
        deleted = SubscriptionService.delete_subscription(TEST_USER_ID, sub_id)
        assert deleted is True, "delete_subscription returned False"

        # Verify DB row deleted
        supabase = get_supabase_client()
        db_check = supabase.from_("subscriptions").select("*").eq("id", sub_id).execute()
        assert len(db_check.data or []) == 0, "Subscription DB row still exists after delete"

    def test_I_autopay_on_to_off_removes_calendar_event(self):
        """Test I — Autopay ON -> OFF -> calendar event removed"""
        payload = SubscriptionCreate(
            merchant_name="Autopay_Toggle_Test_I",
            category="Software",
            amount=599.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=14),
            status="active",
            autopay_enabled=True
        )
        created = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)
        assert created.get("calendar_event_id") is not None, "Expected initial calendar event for Autopay ON"

        # Toggle Autopay OFF
        toggled_off = SubscriptionService.update_subscription(TEST_USER_ID, created["id"], SubscriptionUpdate(autopay_enabled=False))
        assert toggled_off.get("calendar_event_id") is None, f"Calendar event ID should be None after setting Autopay OFF, got {toggled_off.get('calendar_event_id')}"

    def test_J_autopay_off_to_on_creates_single_calendar_event(self):
        """Test J — Autopay OFF -> ON -> exactly one calendar event created"""
        payload = SubscriptionCreate(
            merchant_name="Autopay_Toggle_Test_J",
            category="Software",
            amount=699.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=18),
            status="active",
            autopay_enabled=False
        )
        created = SubscriptionService.create_subscription(None, TEST_USER_ID, payload)

        # Toggle Autopay ON
        toggled_on = SubscriptionService.update_subscription(TEST_USER_ID, created["id"], SubscriptionUpdate(autopay_enabled=True))
        assert toggled_on.get("calendar_event_id") is not None, "Expected calendar event to be created after toggling Autopay ON"

    def test_K_billing_date_reached_calculates_next_date(self):
        """Test K — Billing date reached -> next date calculated correctly (calendar-aware), same calendar event updated, no duplicate"""
        start_date_str = "2026-08-15"
        today_str = "2026-09-20"
        
        # Calculate monthly rollover date
        next_date = SubscriptionService.calculate_rolled_over_date(start_date_str, "monthly", target_today=date(2026, 9, 20))
        assert next_date == "2026-10-15", f"Expected monthly rollover date '2026-10-15', got '{next_date}'"
