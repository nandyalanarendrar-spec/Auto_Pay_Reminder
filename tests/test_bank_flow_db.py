"""End-to-end flow against the real Supabase project, using a throwaway test user (cleaned up afterwards)."""
import os
import sys
import uuid

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import get_supabase_client
from app.routes import bank
from app.services.bank_detection_service import BankDetectionService
from app.services.demo_bank_service import DemoBankService
from app.services.emi_service import EMIService
from app.services.subscription_service import SubscriptionService
from app.services.transaction_store import SOURCE_DEMO, TransactionStore


@pytest.fixture(scope="module")
def user():
    supabase = get_supabase_client()
    email = f"pytest_bank_{uuid.uuid4().hex[:8]}@example.com"
    res = supabase.auth.sign_up({"email": email, "password": "SecurePassword123!"})
    uid = str(res.user.id)
    yield {"id": uid}
    for table in ("detected_items", "transactions", "subscriptions", "emis"):
        try:
            supabase.from_(table).delete().eq("user_id", uid).execute()
        except Exception:
            pass


def _pending(uid):
    return {i["merchant_name"]: i for i in bank.list_detected(status="pending", current_user={"id": uid})["items"]}


def test_1_demo_load_is_idempotent(user):
    uid = user["id"]
    first = DemoBankService.sync(uid)
    assert first > 50
    assert DemoBankService.sync(uid) == 0, "second sync must add nothing"
    assert TransactionStore.count_by_source(uid, SOURCE_DEMO) == first


def test_2_detection_fills_review_list(user):
    uid = user["id"]
    result = BankDetectionService.run(uid)
    assert result["pending"] >= 7
    items = _pending(uid)
    for name in ("Netflix", "Spotify", "Hotstar", "Adobe Creative Cloud", "Room Rent", "Bajaj Finserv EMI", "HDFC Bank Loan"):
        assert name in items, name
    assert "trial_converted" in items["Hotstar"]["flags"]
    assert "price_hike" in items["Adobe Creative Cloud"]["flags"]
    again = BankDetectionService.run(uid)
    assert again["new"] == 0 and again["pending"] == result["pending"], "re-running must not duplicate items"


def test_3_confirm_creates_real_records(user):
    uid = user["id"]
    items = _pending(uid)

    out = bank.confirm_detected(items["Netflix"]["id"], None, current_user={"id": uid})
    assert out["status"] == "confirmed"
    assert any(s["merchant_name"] == "Netflix" for s in SubscriptionService.get_user_subscriptions(uid))

    with pytest.raises(HTTPException) as err:
        bank.confirm_detected(items["HDFC Bank Loan"]["id"], None, current_user={"id": uid})
    assert err.value.status_code == 422, "EMI without a known total must ask the user for it"

    done = bank.confirm_detected(
        items["HDFC Bank Loan"]["id"], bank.ConfirmOverrides(total_installments=36), current_user={"id": uid}
    )
    assert done["created"]["total_installments"] == 36
    assert any(e["loan_name"] == "HDFC Bank Loan" for e in EMIService.get_user_emis(uid))

    bajaj = bank.confirm_detected(items["Bajaj Finserv EMI"]["id"], None, current_user={"id": uid})
    assert bajaj["created"]["total_installments"] == 12

    with pytest.raises(HTTPException) as err:
        bank.confirm_detected(items["Netflix"]["id"], None, current_user={"id": uid})
    assert err.value.status_code == 409, "an item can only be handled once"


def test_4_ignore_and_no_resurrection(user):
    uid = user["id"]
    items = _pending(uid)
    bank.ignore_detected(items["Room Rent"]["id"], current_user={"id": uid})
    BankDetectionService.run(uid)
    remaining = _pending(uid)
    assert "Room Rent" not in remaining, "ignored items must not come back"
    assert "Netflix" not in remaining, "confirmed items must not be suggested again"
    assert "Spotify" in remaining


def test_5_removing_demo_clears_data_and_pending_items(user):
    uid = user["id"]
    out = bank.remove_demo(current_user={"id": uid})
    assert out["removed"] > 50
    assert TransactionStore.count_by_source(uid, SOURCE_DEMO) == 0
    assert _pending(uid) == {}, "pending suggestions built from demo data must disappear"
    # items the user already confirmed stay
    assert any(s["merchant_name"] == "Netflix" for s in SubscriptionService.get_user_subscriptions(uid))
