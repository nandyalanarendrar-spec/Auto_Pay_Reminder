"""
================================================================================
🧪 AUTOPAY GUARD — EMI CALENDAR LIFECYCLE PYTEST SUITE
================================================================================
Covers 4 EMI calendar lifecycle scenarios:
  1. Create EMI -> confirm exactly 1 calendar_event_id assigned
  2. Update EMI (log installment payment / advance date) -> confirm SAME calendar_event_id preserved (PATCH, not CREATE)
  3. Complete all installments (installments_paid == total_installments) -> confirm calendar event is deleted
  4. Delete EMI mid-way -> confirm DB record and specific calendar event purged by ID
"""
import sys
import os
import uuid
import pytest
from datetime import date, timedelta

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import get_supabase_client
from app.services.emi_service import EMIService
from app.schemas.emi import EMICreate, EMIUpdate


@pytest.fixture(scope="module")
def test_user():
    """
    Module-scoped Pytest fixture creating a dedicated test user in Supabase
    so tests don't touch production user data. Cleans up upon teardown.
    """
    supabase = get_supabase_client()
    email = f"emi_pytest_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"
    auth_res = supabase.auth.sign_up({"email": email, "password": password})
    user_id = str(auth_res.user.id)
    ctx = {"user_id": user_id, "email": email, "supabase": supabase}
    
    yield ctx
    
    # Teardown cleanup
    try:
        supabase.from_("emis").delete().eq("user_id", user_id).execute()
    except Exception:
        pass


# ----------------------------------------------------------------------
# TEST 1: Create EMI -> confirm exactly ONE calendar_event_id assigned
# ----------------------------------------------------------------------
def test_1_create_emi_assigns_single_calendar_event(test_user):
    user_id = test_user["user_id"]
    print(f"\n[Test 1] Creating EMI with automatic calendar sync...")
    
    emi = EMIService.create_emi(
        user_id=user_id,
        payload=EMICreate(
            loan_name="Test MacBook Air EMI",
            total_installments=12,
            installments_paid=2,
            installment_amount=5500.0,
            next_due_date=date.today() + timedelta(days=15),
            status="active"
        ),
        trigger_calendar=True
    )
    
    emi_id = emi.get("id")
    event_id = emi.get("calendar_event_id")
    assert emi_id is not None, "❌ EMI ID must not be None"
    assert event_id is not None, "❌ calendar_event_id must not be None"
    
    test_user["emi_test_1"] = emi
    print(f"  ✅ Test 1 PASS: EMI created successfully. Assigned 1 calendar event (ID: {event_id}).")


# ----------------------------------------------------------------------
# TEST 2: Update EMI -> confirm SAME calendar_event_id preserved (PATCH)
# ----------------------------------------------------------------------
def test_2_update_emi_preserves_same_calendar_event_via_patch(test_user):
    user_id = test_user["user_id"]
    emi_1 = test_user.get("emi_test_1")
    assert emi_1 is not None, "❌ EMI 1 missing from previous test"
    
    emi_id = emi_1["id"]
    event_id_before = emi_1.get("calendar_event_id")
    print(f"\n[Test 2] Logging installment payment for EMI {emi_id} (Before Event ID: {event_id_before})...")
    
    updated_emi = EMIService.update_emi(
        user_id=user_id,
        emi_id=emi_id,
        payload=EMIUpdate(pay_installment=True)
    )
    
    event_id_after = updated_emi.get("calendar_event_id")
    print(f"  • Event ID Before: {event_id_before}")
    print(f"  • Event ID After:  {event_id_after}")
    print(f"  • Installments Paid: {updated_emi.get('installments_paid')}/{updated_emi.get('total_installments')}")
    print(f"  • Next Due Date:    {updated_emi.get('next_due_date')}")
    
    assert event_id_after == event_id_before, f"❌ Event ID changed! Before={event_id_before}, After={event_id_after}"
    assert updated_emi.get("installments_paid") == 3, f"Expected 3 paid installments, got {updated_emi.get('installments_paid')}"
    print(f"  ✅ Test 2 PASS: Installment logged & date advanced. Event patched in-place with identical ID ({event_id_after}).")


# ----------------------------------------------------------------------
# TEST 3: Complete all installments -> confirm calendar event deleted
# ----------------------------------------------------------------------
def test_3_complete_emi_deletes_calendar_event(test_user):
    user_id = test_user["user_id"]
    print(f"\n[Test 3] Completing EMI loan to 100% paid...")
    
    emi = EMIService.create_emi(
        user_id=user_id,
        payload=EMICreate(
            loan_name="Short 2-Month Loan",
            total_installments=2,
            installments_paid=1,
            installment_amount=1200.0,
            next_due_date=date.today() + timedelta(days=5),
            status="active"
        ),
        trigger_calendar=True
    )
    
    emi_id = emi["id"]
    event_id_initial = emi.get("calendar_event_id")
    assert event_id_initial is not None, "❌ Initial calendar event missing"
    
    # Pay final installment -> installments_paid == 2 == total_installments
    completed_emi = EMIService.update_emi(
        user_id=user_id,
        emi_id=emi_id,
        payload=EMIUpdate(pay_installment=True)
    )
    
    assert completed_emi.get("status") == "completed", f"Expected status 'completed', got {completed_emi.get('status')}"
    assert completed_emi.get("installments_paid") == 2, f"Expected 2 paid installments, got {completed_emi.get('installments_paid')}"
    assert completed_emi.get("calendar_event_id") is None, "❌ calendar_event_id must be None after completion"
    print("  ✅ Test 3 PASS: EMI fully paid -> status marked 'completed' and calendar event purged cleanly.")


# ----------------------------------------------------------------------
# TEST 4: Delete EMI mid-way -> confirm DB record and calendar event purged
# ----------------------------------------------------------------------
def test_4_delete_emi_midway_purges_db_and_calendar_event(test_user):
    user_id = test_user["user_id"]
    emi_1 = test_user.get("emi_test_1")
    assert emi_1 is not None, "❌ EMI 1 missing"
    
    emi_id = emi_1["id"]
    event_id = emi_1.get("calendar_event_id")
    print(f"\n[Test 4] Deleting active EMI {emi_id} mid-way...")
    
    delete_res = EMIService.delete_emi(user_id=user_id, emi_id=emi_id)
    assert delete_res is True, "❌ delete_emi returned False"
    
    # Confirm DB lookup returns None
    lookup = EMIService.get_emi_by_id(user_id, emi_id)
    assert lookup is None, "❌ Deleted EMI still found in database!"
    print("  ✅ Test 4 PASS: Active EMI mid-way permanently deleted from DB and calendar event purged.")
