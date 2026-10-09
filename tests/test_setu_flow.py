"""Setu connection flow: mapper unit tests plus an end-to-end run with Setu's responses simulated."""
import os
import sys
import uuid
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import get_supabase_client
from app.services import setu_aa_service
from app.services.bank_connection_service import BankConnectionService
from app.services.setu_aa_service import SetuError
from app.services.setu_mapper import extract_merchant, to_transaction_rows
from app.services.transaction_store import SOURCE_SETU, TransactionStore


def _sample_fi_data(today=None):
    today = today or date.today()
    txs = []
    for i, offset in enumerate((100, 70, 40, 10)):
        d = today - timedelta(days=offset)
        txs.append({
            "txnId": f"NFX{i}", "type": "DEBIT", "mode": "UPI", "amount": "649.00",
            "currentBalance": "10000.00", "transactionTimestamp": f"{d.isoformat()}T09:15:00+05:30",
            "valueDate": d.isoformat(), "narration": f"UPI/55512300{i}/NETFLIX COM/netflix@icici/AutoPay",
        })
    txs.append({"txnId": "SAL1", "type": "CREDIT", "mode": "FT", "amount": "50000.00", "currentBalance": "60000.00",
                "transactionTimestamp": f"{(today - timedelta(days=5)).isoformat()}T10:00:00+05:30",
                "valueDate": (today - timedelta(days=5)).isoformat(), "narration": "SALARY CREDIT ACME"})
    txs.append({"txnId": "BAD1", "type": "DEBIT", "mode": "UPI", "amount": "not-a-number",
                "transactionTimestamp": f"{today.isoformat()}T10:00:00+05:30", "narration": "BROKEN ROW"})
    return {
        "id": "session-1", "status": "COMPLETED", "format": "json",
        "fips": [{"fipID": "setu-fip", "accounts": [{
            "FIType": "DEPOSIT", "linkRefNumber": "ref-1", "maskedAccNumber": "XXXXXXXX6298", "status": "READY",
            "data": {"account": {"type": "deposit", "transactions": {"transaction": txs}}},
        }]}],
    }


# --------------------------------------------------------------------------- mapper

def test_extract_merchant_from_common_narrations():
    assert extract_merchant("UPI/548190123456/NETFLIX COM/netflix@icici/AutoPay") == "Netflix"
    assert extract_merchant("ACH DEBIT 4/12 - BAJAJ FINSERV EMI") == "Bajaj Finserv Emi"
    assert extract_merchant("NACH DEBIT - HDFC BANK LOAN EMI") == "Hdfc Loan Emi"
    assert extract_merchant("UPI-SWIGGY-swiggy@ybl-123456") == "Swiggy"
    assert extract_merchant("") == "Unknown"
    assert extract_merchant("1234567890") == "Unknown"
    # formats seen in Setu's sandbox: MODE/CR|DE/reference/name/code/number
    assert extract_merchant("CASH/DE/811516823632/Dishani Deshpande/TBVV/1") == "Dishani Deshpande"
    assert extract_merchant("CARD/CR/900031694348/Shamik Kaur/SIJQ/7219210") == "Shamik Kaur"
    assert extract_merchant("ATM/DE/123456789012") == "Unknown"


def test_mapper_keeps_only_valid_debits_with_stable_ids():
    rows = to_transaction_rows(_sample_fi_data(), "user-1")
    assert len(rows) == 4, "credits and unreadable rows must be dropped"
    assert all(r["source"] == SOURCE_SETU and r["merchant_name"] == "Netflix" for r in rows)
    assert all(r["external_id"].startswith("setu:XXXXXXXX6298:") for r in rows)
    again = to_transaction_rows(_sample_fi_data(), "user-1")
    assert [r["external_id"] for r in rows] == [r["external_id"] for r in again]


def test_mapper_tolerates_empty_or_odd_responses():
    assert to_transaction_rows({}, "u") == []
    assert to_transaction_rows({"fips": [{"accounts": [{"maskedAccNumber": "X1", "data": {}}]}]}, "u") == []
    assert to_transaction_rows({"fips": [{"accounts": [{"data": {"account": {"transactions": []}}}]}]}, "u") == []


def test_mobile_validation():
    assert BankConnectionService.validate_mobile("+91 98765 43210") == "9876543210"
    assert BankConnectionService.validate_mobile("09876543210"[1:]) == "9876543210"
    for bad in ("12345", "1234567890", "abcdefghij", ""):
        with pytest.raises(ValueError):
            BankConnectionService.validate_mobile(bad)


def test_setu_client_trims_credentials_and_reports_unconfigured(monkeypatch):
    monkeypatch.setattr(setu_aa_service.settings, "SETU_CLIENT_SECRET", "")
    assert setu_aa_service.is_configured() is False
    with pytest.raises(SetuError) as err:
        setu_aa_service._request("GET", "/v2/consents/x")
    assert err.value.status == 503
    assert setu_aa_service._clean("  abc\n") == "abc"


# --------------------------------------------------------------------------- end to end (Setu simulated)

@pytest.fixture(scope="module")
def user():
    supabase = get_supabase_client()
    email = f"pytest_setu_{uuid.uuid4().hex[:8]}@example.com"
    res = supabase.auth.sign_up({"email": email, "password": "SecurePassword123!"})
    uid = str(res.user.id)
    yield {"id": uid}
    for table in ("detected_items", "transactions", "bank_consents", "subscriptions", "emis"):
        try:
            supabase.from_(table).delete().eq("user_id", uid).execute()
        except Exception:
            pass


@pytest.fixture
def fake_setu(monkeypatch):
    state = {"consent_status": "PENDING", "revoked": [], "sessions": 0}
    cid = f"consent-{uuid.uuid4().hex[:8]}"

    def create_consent(mobile, data_from, data_to):
        assert mobile == "9876543210" and data_from < data_to
        return {"id": cid, "url": f"https://fiu-uat.setu.co/v2/consents/ui/{cid}", "status": "PENDING"}

    def get_consent(consent_id):
        assert consent_id == cid
        linked = [{"maskedAccNumber": "XXXXXXXX6298", "accType": "SAVINGS", "fipId": "setu-fip"}] if state["consent_status"] == "ACTIVE" else []
        return {"id": cid, "status": state["consent_status"], "accountsLinked": linked}

    def create_session(consent_id, data_from, data_to):
        state["sessions"] += 1
        return {"id": f"sess-{state['sessions']}", "status": "PENDING"}

    monkeypatch.setattr(setu_aa_service, "is_configured", lambda: True)
    monkeypatch.setattr(setu_aa_service, "create_consent", create_consent)
    monkeypatch.setattr(setu_aa_service, "get_consent", get_consent)
    monkeypatch.setattr(setu_aa_service, "create_session", create_session)
    monkeypatch.setattr(setu_aa_service, "get_session", lambda sid: _sample_fi_data())
    monkeypatch.setattr(setu_aa_service, "revoke_consent", lambda c: state["revoked"].append(c) or {})
    state["consent_id"] = cid
    return state


def test_1_connect_returns_approval_link_and_stores_pending_consent(user, fake_setu):
    out = BankConnectionService.connect(user["id"], "98765 43210")
    assert out["consent_id"] == fake_setu["consent_id"] and out["url"].startswith("https://")
    status = BankConnectionService.status(user["id"])
    assert status["state"] == "pending" and status["phone_masked"] == "XXXXXX3210"
    assert status["consent_url"] == out["url"]
    with pytest.raises(SetuError) as err:
        BankConnectionService.sync(user["id"])
    assert err.value.status == 409, "cannot fetch data before the user approves"


def test_2_webhook_activates_and_imports_then_detects(user, fake_setu):
    BankConnectionService.connect(user["id"], "9876543210")
    fake_setu["consent_status"] = "ACTIVE"
    result = BankConnectionService.handle_webhook({"type": "CONSENT_STATUS_UPDATE", "data": {"consentId": fake_setu["consent_id"], "status": "ACTIVE"}})
    assert result["handled"] == 1
    assert BankConnectionService.status(user["id"])["state"] == "active"
    imported = TransactionStore.get_user_transactions(user["id"], source=SOURCE_SETU)
    assert len(imported) == 4
    pending = get_supabase_client().from_("detected_items").select("merchant_name").eq("user_id", user["id"]).eq("status", "pending").execute().data
    assert [p["merchant_name"] for p in pending] == ["Netflix"], "real-looking narrations must lead to a Netflix suggestion"


def test_3_second_sync_adds_nothing_and_unknown_webhooks_are_ignored(user, fake_setu):
    BankConnectionService.connect(user["id"], "9876543210")
    fake_setu["consent_status"] = "ACTIVE"
    BankConnectionService.handle_webhook({"consentId": fake_setu["consent_id"]})
    again = BankConnectionService.sync(user["id"])
    assert again["fetched"] == 4 and again["added"] == 0
    assert BankConnectionService.handle_webhook({"consentId": "not-ours", "x": [1, 2]}) == {"handled": 0}
    assert BankConnectionService.handle_webhook("garbage") == {"handled": 0}


def test_4_disconnect_revokes_and_removes_imported_data(user, fake_setu):
    BankConnectionService.connect(user["id"], "9876543210")
    fake_setu["consent_status"] = "ACTIVE"
    BankConnectionService.sync(user["id"])
    out = BankConnectionService.disconnect(user["id"])
    assert out["removed_transactions"] == 4
    assert fake_setu["consent_id"] in fake_setu["revoked"]
    assert BankConnectionService.status(user["id"])["state"] == "not_connected"
    assert TransactionStore.count_by_source(user["id"], SOURCE_SETU) == 0


def test_5_daily_limit_gives_a_friendly_message(user, fake_setu, monkeypatch):
    BankConnectionService.connect(user["id"], "9876543210")
    fake_setu["consent_status"] = "ACTIVE"

    def too_many(consent_id, data_from, data_to):
        raise SetuError("Consent use exceeded", 400)

    monkeypatch.setattr(setu_aa_service, "create_session", too_many)
    with pytest.raises(SetuError) as err:
        BankConnectionService.sync(user["id"])
    assert err.value.status == 429 and "tomorrow" in str(err.value)
    BankConnectionService.disconnect(user["id"])


def test_6_daily_job_skips_connections_synced_recently(user, fake_setu):
    calls = []
    original = BankConnectionService.sync
    BankConnectionService.sync = staticmethod(lambda uid: calls.append(uid) or {})
    try:
        BankConnectionService.connect(user["id"], "9876543210")
        fake_setu["consent_status"] = "ACTIVE"
        BankConnectionService.refresh(BankConnectionService.latest(user["id"]))
        result = BankConnectionService.run_daily_for_all()
        assert user["id"] in calls, "never-synced connection must be picked up"
        calls.clear()
        from datetime import datetime, timezone
        get_supabase_client().from_("bank_consents").update(
            {"last_synced_at": datetime.now(timezone.utc).isoformat()}
        ).eq("user_id", user["id"]).execute()
        BankConnectionService.run_daily_for_all()
        assert user["id"] not in calls, "a connection synced a minute ago must be skipped"
    finally:
        BankConnectionService.sync = original
        BankConnectionService.disconnect(user["id"])


def test_error_text_explains_non_json_replies():
    class FakeResponse:
        status_code = 403
        text = "<html><body><h1>Access denied</h1><p>Error 1010 browser signature banned</p></body></html>"
        headers = {"server": "cloudflare"}

        def json(self):
            raise ValueError("not json")

    message = setu_aa_service._error_text(FakeResponse())
    assert "403" in message and "cloudflare" in message and "Access denied" in message and "<" not in message
