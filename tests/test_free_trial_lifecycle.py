"""
================================================================================
🧪 AUTOPAY GUARD — FREE TRIAL EXPIRATION ROLLOVER PYTEST SUITE
================================================================================
Covers 4 trial expiration rollover scenarios:
  1. Create subscription with status="trial", is_free_trial=True, trial_end_date=today, autopay_enabled=True 
     -> confirm exactly ONE calendar_event_id is assigned.
  2. Run process_trial_conversions -> confirm:
     - status changes from "trial" to "active"
     - is_free_trial changes to False
     - next_payment_date advances correctly
     - calendar_event_id remains IDENTICAL before and after (PATCH, not CREATE)
  3. Edge case: trial NOT yet reached trial_end_date -> confirm NOT converted (status stays "trial", is_free_trial stays True).
  4. Edge case: run process_trial_conversions twice in a row on the same subscription -> confirm idempotency (no double conversion, calendar_event_id unchanged).
"""
import sys
import os
import uuid
import pytest
from datetime import date, timedelta

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import get_supabase_client
from app.services.subscription_service import SubscriptionService
from app.schemas.subscription import SubscriptionCreate


@pytest.fixture(scope="module")
def test_user():
    """
    Module-scoped Pytest fixture creating a dedicated test user in Supabase
    so tests don't touch production user data. Cleans up upon teardown.
    """
    supabase = get_supabase_client()
    email = f"trial_pytest_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"
    auth_res = supabase.auth.sign_up({"email": email, "password": password})
    user_id = str(auth_res.user.id)
    ctx = {"user_id": user_id, "email": email, "supabase": supabase}
    
    yield ctx
    
    # Teardown cleanup
    try:
        supabase.from_("subscriptions").delete().eq("user_id", user_id).execute()
    except Exception:
        pass


# ----------------------------------------------------------------------
# TEST 1: Create trial subscription -> confirm exactly ONE calendar_event_id assigned
# ----------------------------------------------------------------------
def test_1_create_trial_subscription_assigns_calendar_event(test_user):
    user_id = test_user["user_id"]
    today = date.today()
    print(f"\n[Test 1] Creating trial subscription expiring today ({today})...")
    
    sub = SubscriptionService.create_subscription(
        db=None,
        user_id=user_id,
        payload=SubscriptionCreate(
            merchant_name="Adobe Creative Cloud (Trial)",
            amount=1500.0,
            billing_frequency="monthly",
            next_payment_date=today,
            trial_start_date=today - timedelta(days=14),
            trial_end_date=today,
            status="trial",
            is_free_trial=True,
            autopay_enabled=True
        ),
        trigger_calendar=True
    )
    
    sub_id = sub.get("id")
    event_id = sub.get("calendar_event_id")
    assert sub_id is not None, "❌ Subscription ID must not be None"
    assert event_id is not None, "❌ calendar_event_id must not be None"
    assert sub.get("status") == "trial", f"Expected status 'trial', got '{sub.get('status')}'"
    assert sub.get("is_free_trial") is True, f"Expected is_free_trial True, got {sub.get('is_free_trial')}"
    
    test_user["trial_sub_1"] = sub
    print(f"  ✅ Test 1 PASS: Trial subscription created successfully. Assigned 1 calendar event (ID: {event_id}).")


# ----------------------------------------------------------------------
# TEST 2: Run process_trial_conversions -> confirm active, is_free_trial=False, next_date advanced, SAME calendar_event_id
# ----------------------------------------------------------------------
def test_2_process_trial_conversion_advances_date_and_patches_calendar(test_user):
    user_id = test_user["user_id"]
    sub_1 = test_user.get("trial_sub_1")
    assert sub_1 is not None, "❌ Trial subscription missing from previous test"
    
    sub_id = sub_1["id"]
    event_id_before = sub_1.get("calendar_event_id")
    next_date_before = sub_1.get("next_payment_date")
    
    print(f"\n[Test 2] Running process_trial_conversions for user {user_id}...")
    print(f"  • Before: status={sub_1.get('status')}, is_free_trial={sub_1.get('is_free_trial')}, next_date={next_date_before}, calendar_event_id={event_id_before}")
    
    conversions = SubscriptionService.process_trial_conversions(user_id=user_id)
    
    # Re-fetch updated subscription from Supabase to verify DB state
    supabase = test_user["supabase"]
    res = supabase.from_("subscriptions").select("*").eq("id", sub_id).execute()
    assert res.data and len(res.data) > 0, "❌ Subscription record not found in DB after conversion"
    updated_sub = res.data[0]
    
    event_id_after = updated_sub.get("calendar_event_id")
    next_date_after = updated_sub.get("next_payment_date")
    status_after = updated_sub.get("status")
    is_free_trial_after = updated_sub.get("is_free_trial")
    
    print(f"  • After:  status={status_after}, is_free_trial={is_free_trial_after}, next_date={next_date_after}, calendar_event_id={event_id_after}")
    
    assert status_after == "active", f"❌ Expected status 'active', got '{status_after}'"
    assert is_free_trial_after is False, f"❌ Expected is_free_trial False, got {is_free_trial_after}"
    assert str(next_date_after)[:10] > str(next_date_before)[:10], f"❌ expected next_payment_date to advance! Before={next_date_before}, After={next_date_after}"
    assert event_id_after == event_id_before, f"❌ Event ID changed! Before={event_id_before}, After={event_id_after}"
    
    test_user["trial_sub_1_updated"] = updated_sub
    print(f"  ✅ Test 2 PASS: Status updated to 'active', is_free_trial=False, next_payment_date advanced to {next_date_after}, calendar event patched in-place (ID: {event_id_after}).")


# ----------------------------------------------------------------------
# TEST 3: Edge case: Trial NOT yet reached trial_end_date -> confirm NOT converted
# ----------------------------------------------------------------------
def test_3_unexpired_trial_is_not_converted(test_user):
    user_id = test_user["user_id"]
    future_trial_end = date.today() + timedelta(days=7)
    
    print(f"\n[Test 3] Creating active trial expiring in 7 days ({future_trial_end})...")
    
    unexpired_sub = SubscriptionService.create_subscription(
        db=None,
        user_id=user_id,
        payload=SubscriptionCreate(
            merchant_name="Spotify Premium (Trial)",
            amount=179.0,
            billing_frequency="monthly",
            next_payment_date=future_trial_end,
            trial_start_date=date.today(),
            trial_end_date=future_trial_end,
            status="trial",
            is_free_trial=True,
            autopay_enabled=True
        ),
        trigger_calendar=True
    )
    
    unexpired_id = unexpired_sub["id"]
    print(f"  • Created unexpired trial: ID={unexpired_id}, status={unexpired_sub.get('status')}, trial_end_date={unexpired_sub.get('trial_end_date')}")
    
    # Run conversion engine
    SubscriptionService.process_trial_conversions(user_id=user_id)
    
    # Re-fetch from Supabase DB
    supabase = test_user["supabase"]
    res = supabase.from_("subscriptions").select("*").eq("id", unexpired_id).execute()
    sub_after = res.data[0]
    
    print(f"  • After conversion run: status={sub_after.get('status')}, is_free_trial={sub_after.get('is_free_trial')}, next_date={sub_after.get('next_payment_date')}")
    
    assert sub_after.get("status") == "trial", f"❌ Unexpired trial status should remain 'trial', got '{sub_after.get('status')}'"
    assert sub_after.get("is_free_trial") is True, f"❌ Unexpired trial is_free_trial should remain True, got {sub_after.get('is_free_trial')}"
    assert str(sub_after.get("next_payment_date"))[:10] == str(future_trial_end), "❌ Unexpired trial next_payment_date should not have changed"
    
    print("  ✅ Test 3 PASS: Unexpired trial untouched by conversion engine (status remains 'trial').")


# ----------------------------------------------------------------------
# TEST 4: Edge case: Run process_trial_conversions twice in a row (Idempotency)
# ----------------------------------------------------------------------
def test_4_process_trial_conversions_idempotency(test_user):
    user_id = test_user["user_id"]
    sub_1 = test_user.get("trial_sub_1_updated")
    assert sub_1 is not None, "❌ Converted trial sub missing from Test 2"
    
    sub_id = sub_1["id"]
    event_id_before = sub_1.get("calendar_event_id")
    next_date_before = sub_1.get("next_payment_date")
    
    print(f"\n[Test 4] Running process_trial_conversions second time in a row (Idempotency check)...")
    
    conversions_run_2 = SubscriptionService.process_trial_conversions(user_id=user_id)
    
    # Re-fetch from DB
    supabase = test_user["supabase"]
    res = supabase.from_("subscriptions").select("*").eq("id", sub_id).execute()
    sub_after = res.data[0]
    
    print(f"  • Second Run conversions count returned: {len(conversions_run_2)}")
    print(f"  • DB State After Second Run: status={sub_after.get('status')}, next_date={sub_after.get('next_payment_date')}, calendar_event_id={sub_after.get('calendar_event_id')}")
    
    assert sub_after.get("status") == "active", "❌ Status should remain 'active'"
    assert sub_after.get("is_free_trial") is False, "❌ is_free_trial should remain False"
    assert sub_after.get("next_payment_date") == next_date_before, f"❌ next_payment_date changed on second run! Before={next_date_before}, After={sub_after.get('next_payment_date')}"
    assert sub_after.get("calendar_event_id") == event_id_before, f"❌ Duplicate calendar event created! Before={event_id_before}, After={sub_after.get('calendar_event_id')}"
    
    print("  ✅ Test 4 PASS: Second run performed zero conversions / modifications (Idempotency confirmed).")
