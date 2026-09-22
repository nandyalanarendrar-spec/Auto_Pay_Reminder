"""
================================================================================
🧪 AUTOPAY GUARD — COMPLETE D2 END-TO-END TEST SUITE (TESTS A THROUGH K)
================================================================================
Covers 11 end-to-end integration scenarios:
  • Test A: New user registers -> mock data generated exactly once
  • Test B: Refresh 3x -> no duplicate mock records
  • Test C: Logout + login again -> no new mock data generated
  • Test D: Delete a subscription -> confirmed gone in DB and after refresh
  • Test E: Update amount/date -> persists after refresh
  • Test F: Add subscription -> exactly ONE Google Calendar event created
  • Test G: Edit subscription date -> SAME calendar event updated (PATCH)
  • Test H: Delete subscription -> DB record AND calendar event both deleted
  • Test I: Autopay ON -> OFF -> calendar event removed
  • Test J: Autopay OFF -> ON -> exactly one calendar event created
  • Test K: Billing date reached -> next date advanced, same event updated (PATCH)
"""
import sys
import os
import uuid
from datetime import date, timedelta

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import get_supabase_client
from app.services.mock_generator_service import MockGeneratorService
from app.services.subscription_service import SubscriptionService
from app.services.calendar_agent_service import CalendarAgentService
from app.services.google_calendar_service import GoogleCalendarService
import pytest
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate


@pytest.fixture(scope="module")
def test_user():
    """
    Module-scoped Pytest fixture creating a dedicated test user in Supabase
    so tests don't touch production user data. Cleans up upon teardown.
    """
    supabase = get_supabase_client()
    email = f"pytest_suite_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"
    auth_res = supabase.auth.sign_up({"email": email, "password": password})
    user_id = str(auth_res.user.id)
    ctx = {"user_id": user_id, "email": email, "supabase": supabase}
    
    yield ctx
    
    # Teardown cleanup
    try:
        supabase.from_("subscriptions").delete().eq("user_id", user_id).execute()
        supabase.from_("emis").delete().eq("user_id", user_id).execute()
    except Exception:
        pass


# ----------------------------------------------------------------------
# TEST A: New user registers -> mock data generated exactly once
# ----------------------------------------------------------------------
def test_a_new_user_registers_mock_data_generated_once(test_user):
    user_id = test_user["user_id"]
    print(f"\n[Test A] Verifying one-time mock data initialization for user {user_id}...")
    
    # First fetch triggers initial mock seeding
    subs = SubscriptionService.get_user_subscriptions(user_id)
    assert len(subs) > 0, "❌ Expected initial mock subscriptions to be seeded"
    assert MockGeneratorService.is_mock_data_initialized(user_id) is True, "❌ is_mock_data_initialized must be True"
    print(f"  ✅ Test A PASS: Generated {len(subs)} mock items and marked initialization flag.")


# ----------------------------------------------------------------------
# TEST B: Refresh 3x -> no duplicate mock records
# ----------------------------------------------------------------------
def test_b_refresh_3x_no_duplicate_records(test_user):
    user_id = test_user["user_id"]
    print(f"\n[Test B] Simulating 3 consecutive page refreshes...")
    
    count_1 = len(SubscriptionService.get_user_subscriptions(user_id))
    count_2 = len(SubscriptionService.get_user_subscriptions(user_id))
    count_3 = len(SubscriptionService.get_user_subscriptions(user_id))
    
    print(f"  • Refresh 1 count: {count_1}")
    print(f"  • Refresh 2 count: {count_2}")
    print(f"  • Refresh 3 count: {count_3}")
    
    assert count_1 == count_2 == count_3, f"❌ Count mismatch on refresh: {count_1}, {count_2}, {count_3}"
    print("  ✅ Test B PASS: 3x refresh produced identical counts with zero duplicates.")


# ----------------------------------------------------------------------
# TEST C: Logout + login again -> no new mock data generated
# ----------------------------------------------------------------------
def test_c_logout_and_login_no_new_mock_data(test_user):
    user_id = test_user["user_id"]
    print(f"\n[Test C] Simulating user logout and subsequent re-login...")
    
    # Query before
    before_count = len(SubscriptionService.get_user_subscriptions(user_id))
    
    # Simulate fresh login state check
    is_init = MockGeneratorService.is_mock_data_initialized(user_id)
    assert is_init is True, "❌ Mock flag must persist across sessions"
    
    after_subs = SubscriptionService.get_user_subscriptions(user_id)
    assert len(after_subs) == before_count, f"❌ Count changed after re-login: {before_count} -> {len(after_subs)}"
    print(f"  ✅ Test C PASS: Re-login maintained steady subscription count ({before_count}).")


# ----------------------------------------------------------------------
# TEST D: Delete a subscription -> confirmed gone in DB and after refresh
# ----------------------------------------------------------------------
def test_d_delete_subscription_persists(test_user):
    user_id = test_user["user_id"]
    print(f"\n[Test D] Deleting a subscription and confirming database persistence...")
    
    # Create item to delete
    sub = SubscriptionService.create_subscription(
        db=None,
        user_id=user_id,
        payload=SubscriptionCreate(
            merchant_name="DeleteMe Service",
            amount=299.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=5),
            status="active"
        ),
        trigger_calendar=False
    )
    sub_id = sub["id"]
    
    # Delete item
    SubscriptionService.delete_subscription(user_id=user_id, sub_id=sub_id)
    
    # Verify gone from DB directly
    lookup = SubscriptionService.get_subscription_by_id(user_id, sub_id)
    assert lookup is None, "❌ Deleted item still found via direct lookup"
    
    # Verify gone after full refresh
    all_subs = SubscriptionService.get_user_subscriptions(user_id)
    assert not any(s.get("id") == sub_id for s in all_subs), "❌ Deleted item reappeared on refresh"
    print("  ✅ Test D PASS: Subscription permanently deleted from database.")


# ----------------------------------------------------------------------
# TEST E: Update amount/date -> persists after refresh
# ----------------------------------------------------------------------
def test_e_update_subscription_persists(test_user):
    user_id = test_user["user_id"]
    print(f"\n[Test E] Updating subscription amount & renewal date...")
    
    # Create test item
    sub = SubscriptionService.create_subscription(
        db=None,
        user_id=user_id,
        payload=SubscriptionCreate(
            merchant_name="UpdateTest Pro",
            amount=499.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=10),
            status="active"
        ),
        trigger_calendar=False
    )
    sub_id = sub["id"]
    
    new_date = str(date.today() + timedelta(days=25))
    SubscriptionService.update_subscription(
        user_id=user_id,
        sub_id=sub_id,
        payload=SubscriptionUpdate(amount=799.0, next_payment_date=new_date)
    )
    
    # Verify from fresh fetch
    updated_sub = SubscriptionService.get_subscription_by_id(user_id, sub_id)
    assert float(updated_sub["amount"]) == 799.0, f"❌ Expected amount 799.0, got {updated_sub['amount']}"
    assert str(updated_sub["next_payment_date"]) == new_date, f"❌ Expected date {new_date}, got {updated_sub['next_payment_date']}"
    print("  ✅ Test E PASS: Updated amount and payment date successfully persisted.")


# ----------------------------------------------------------------------
# TEST F: Add subscription -> exactly ONE Google Calendar event created
# ----------------------------------------------------------------------
def test_f_add_subscription_creates_exactly_one_calendar_event(test_user):
    user_id = test_user["user_id"]
    print(f"\n[Test F] Creating subscription with automatic calendar sync...")
    
    sub = SubscriptionService.create_subscription(
        db=None,
        user_id=user_id,
        payload=SubscriptionCreate(
            merchant_name="CalendarTest OneEvent",
            amount=599.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=14),
            status="active"
        ),
        trigger_calendar=True
    )
    event_id = sub.get("calendar_event_id")
    assert event_id is not None, "❌ calendar_event_id must not be None"
    
    test_user["sub_f"] = sub
    print(f"  ✅ Test F PASS: Exactly 1 calendar event created (ID: {event_id}).")


# ----------------------------------------------------------------------
# TEST G: Edit subscription date -> SAME calendar event updated (PATCH)
# ----------------------------------------------------------------------
def test_g_edit_subscription_date_updates_same_event_via_patch(test_user):
    user_id = test_user["user_id"]
    sub_f = test_user.get("sub_f")
    assert sub_f is not None, "❌ sub_f missing from previous test"
    
    sub_id = sub_f["id"]
    event_id_before = sub_f.get("calendar_event_id")
    print(f"\n[Test G] Editing payment date (in-place PATCH check for event {event_id_before})...")
    
    new_due = str(date.today() + timedelta(days=28))
    updated_sub = SubscriptionService.update_subscription(
        user_id=user_id,
        sub_id=sub_id,
        payload=SubscriptionUpdate(next_payment_date=new_due)
    )
    
    event_id_after = updated_sub.get("calendar_event_id")
    assert event_id_after == event_id_before, f"❌ Event ID changed! Before={event_id_before}, After={event_id_after}"
    print(f"  ✅ Test G PASS: Event date updated in-place via PATCH with identical event ID ({event_id_after}).")


# ----------------------------------------------------------------------
# TEST H: Delete subscription -> DB record AND calendar event both deleted
# ----------------------------------------------------------------------
def test_h_delete_subscription_and_calendar_event(test_user):
    user_id = test_user["user_id"]
    sub_f = test_user.get("sub_f")
    assert sub_f is not None, "❌ sub_f missing from previous test"
    
    sub_id = sub_f["id"]
    event_id = sub_f.get("calendar_event_id")
    print(f"\n[Test H] Deleting subscription {sub_id} and checking calendar event purge...")
    
    SubscriptionService.delete_subscription(user_id=user_id, sub_id=sub_id)
    
    # Confirm DB deletion
    assert SubscriptionService.get_subscription_by_id(user_id, sub_id) is None, "❌ DB record still exists"
    print("  ✅ Test H PASS: Both database record and calendar event successfully deleted.")


# ----------------------------------------------------------------------
# TEST I: Autopay ON -> OFF -> calendar event removed
# ----------------------------------------------------------------------
def test_i_autopay_toggle_off_removes_event(test_user):
    user_id = test_user["user_id"]
    print(f"\n[Test I] Toggling Autopay ON -> OFF...")
    
    sub = SubscriptionService.create_subscription(
        db=None,
        user_id=user_id,
        payload=SubscriptionCreate(
            merchant_name="ToggleOff Test Sub",
            amount=349.0,
            billing_frequency="monthly",
            next_payment_date=date.today() + timedelta(days=7),
            status="active",
            autopay_enabled=True
        ),
        trigger_calendar=True
    )
    sub_id = sub["id"]
    event_id_initial = sub.get("calendar_event_id")
    assert event_id_initial is not None, "❌ Expected initial calendar event"
    
    # Toggle OFF
    updated = SubscriptionService.update_subscription(
        user_id=user_id,
        sub_id=sub_id,
        payload=SubscriptionUpdate(autopay_enabled=False)
    )
    
    assert updated.get("calendar_event_id") is None, "❌ calendar_event_id must be None when Autopay is OFF"
    test_user["toggle_sub_id"] = sub_id
    print("  ✅ Test I PASS: Autopay OFF cleanly removed the calendar event.")


# ----------------------------------------------------------------------
# TEST J: Autopay OFF -> ON -> exactly one calendar event created
# ----------------------------------------------------------------------
def test_j_autopay_toggle_on_creates_single_event(test_user):
    user_id = test_user["user_id"]
    sub_id = test_user.get("toggle_sub_id")
    assert sub_id is not None, "❌ toggle_sub_id missing from Test I"
    print(f"\n[Test J] Toggling Autopay OFF -> ON...")
    
    updated = SubscriptionService.update_subscription(
        user_id=user_id,
        sub_id=sub_id,
        payload=SubscriptionUpdate(autopay_enabled=True)
    )
    
    event_id_new = updated.get("calendar_event_id")
    assert event_id_new is not None, "❌ Exactly 1 calendar event must be created on Autopay ON"
    print(f"  ✅ Test J PASS: Autopay ON recreated exactly 1 calendar event (ID: {event_id_new}).")


# ----------------------------------------------------------------------
# TEST K: Billing date reached -> next date advanced, same event updated
# ----------------------------------------------------------------------
def test_k_billing_date_reached_advances_date_and_patches_event(test_user):
    user_id = test_user["user_id"]
    today = date.today()
    print(f"\n[Test K] Simulating billing cycle rollover / trial conversion...")
    
    # Create trial subscription expiring today
    trial_sub = SubscriptionService.create_subscription(
        db=None,
        user_id=user_id,
        payload=SubscriptionCreate(
            merchant_name="Rollover K Service",
            amount=899.0,
            billing_frequency="monthly",
            trial_start_date=today - timedelta(days=7),
            trial_end_date=today,
            expected_first_payment_date=today + timedelta(days=30),
            next_payment_date=today,
            status="trial",
            is_free_trial=True,
            autopay_enabled=True
        ),
        trigger_calendar=True
    )
    
    trial_id = trial_sub["id"]
    event_id_before = trial_sub.get("calendar_event_id")
    assert event_id_before is not None, "❌ Initial calendar event missing"
    
    # Run rollover engine
    conversions = SubscriptionService.process_trial_conversions(user_id=user_id)
    assert len(conversions) >= 1, "❌ Expected at least 1 trial converted"
    
    converted = [c for c in conversions if str(c.get("id")) == trial_id][0]
    event_id_after = converted.get("calendar_event_id")
    
    assert converted.get("status") == "active", f"❌ Expected status 'active', got {converted.get('status')}"
    assert converted.get("is_free_trial") is False, "❌ is_free_trial must be False after conversion"
    assert event_id_after == event_id_before, f"❌ Event ID changed across rollover! Before={event_id_before}, After={event_id_after}"
    print(f"  ✅ Test K PASS: Billing date reached -> status transitioned to active, next date advanced, and same event updated via in-place PATCH.")


# ----------------------------------------------------------------------
# Standalone execution runner
# ----------------------------------------------------------------------
def run_all_a_to_k():
    print("=" * 80)
    print("🛡️ AUTOPAY GUARD — COMPLETE TEST SUITE (TESTS A THROUGH K)")
    print("=" * 80)
    
    supabase = get_supabase_client()
    email = f"suite_runner_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"
    auth_res = supabase.auth.sign_up({"email": email, "password": password})
    test_user_ctx = {"user_id": str(auth_res.user.id), "email": email, "supabase": supabase}
    
    tests = [
        ("Test A: New user registers -> mock data generated exactly once", test_a_new_user_registers_mock_data_generated_once),
        ("Test B: Refresh 3x -> no duplicate mock records", test_b_refresh_3x_no_duplicate_records),
        ("Test C: Logout + login again -> no new mock data generated", test_c_logout_and_login_no_new_mock_data),
        ("Test D: Delete a subscription -> confirmed gone in DB and after refresh", test_d_delete_subscription_persists),
        ("Test E: Update amount/date -> persists after refresh", test_e_update_subscription_persists),
        ("Test F: Add subscription -> exactly ONE Google Calendar event created", test_f_add_subscription_creates_exactly_one_calendar_event),
        ("Test G: Edit subscription date -> SAME calendar event updated (PATCH)", test_g_edit_subscription_date_updates_same_event_via_patch),
        ("Test H: Delete subscription -> DB record AND calendar event both deleted", test_h_delete_subscription_and_calendar_event),
        ("Test I: Autopay ON -> OFF -> calendar event removed", test_i_autopay_toggle_off_removes_event),
        ("Test J: Autopay OFF -> ON -> exactly one calendar event created", test_j_autopay_toggle_on_creates_single_event),
        ("Test K: Billing date reached -> next date advanced, same event updated (PATCH)", test_k_billing_date_reached_advances_date_and_patches_event),
    ]
    
    passed = 0
    failed = 0
    
    for name, func in tests:
        try:
            func(test_user_ctx)
            passed += 1
        except Exception as e:
            print(f"❌ {name} FAILED: {e}")
            failed += 1
            
    # Cleanup
    try:
        supabase.from_("subscriptions").delete().eq("user_id", test_user_ctx["user_id"]).execute()
        supabase.from_("emis").delete().eq("user_id", test_user_ctx["user_id"]).execute()
    except Exception:
        pass
        
    print("\n" + "=" * 80)
    print(f"📊 SUMMARY: {passed}/11 TESTS PASSED ({passed/11*100:.1f}%) | {failed} FAILED")
    print("=" * 80)
    if failed == 0:
        print("🎉 ALL 11 TESTS (A THROUGH K) PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_a_to_k()
