"""WhatsApp alerts must go only to the user they are about, never to a shared test number."""
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.services import whatsapp_service
from app.services.firebase_notification_service import FirebaseNotificationService
from app.services.whatsapp_service import WhatsAppService

SHARED_TEST_NUMBER = "919014220155"
ITEM = {
    "id": "item-1", "type": "subscription", "name": "Netflix", "amount": 649, "next_due_date": "2026-10-20",
    "days_remaining": 3, "urgency": "HIGH", "notification_type": "3d", "title": "Netflix due", "body": "in 3 days",
    "is_free_trial": False,
}


@pytest.fixture(autouse=True)
def clear_phone_cache():
    whatsapp_service._phone_cache.clear()
    yield
    whatsapp_service._phone_cache.clear()


def _fake_supabase(metadata=None, raises=False):
    def get_user_by_id(uid):
        if raises:
            raise RuntimeError("boom")
        return types.SimpleNamespace(user=types.SimpleNamespace(user_metadata=metadata))

    admin = types.SimpleNamespace(get_user_by_id=get_user_by_id)
    return types.SimpleNamespace(auth=types.SimpleNamespace(admin=admin))


def test_normalize_user_phone():
    assert WhatsAppService.normalize_user_phone("+91 98765 43210") == "919876543210"
    assert WhatsAppService.normalize_user_phone("9876543210") == "919876543210"
    assert WhatsAppService.normalize_user_phone("919876543210") == "919876543210"
    for bad in ("", None, "12345", "abc", "1" * 20):
        assert WhatsAppService.normalize_user_phone(bad) is None


def test_resolve_returns_the_users_own_number(monkeypatch):
    import app.core.security as security
    monkeypatch.setattr(security, "get_supabase_client", lambda: _fake_supabase({"phone_number": "+91 90000 11111"}))
    assert WhatsAppService.resolve_user_phone("user-a") == "919000011111"


def test_resolve_returns_none_without_a_number_and_never_the_default(monkeypatch):
    import app.core.security as security
    monkeypatch.setattr(security, "get_supabase_client", lambda: _fake_supabase({"full_name": "No Phone"}))
    assert WhatsAppService.resolve_user_phone("user-b") is None
    assert WhatsAppService.resolve_user_phone("") is None


def test_lookup_failure_is_not_cached(monkeypatch):
    import app.core.security as security
    monkeypatch.setattr(security, "get_supabase_client", lambda: _fake_supabase(raises=True))
    assert WhatsAppService.resolve_user_phone("user-c") is None
    monkeypatch.setattr(security, "get_supabase_client", lambda: _fake_supabase({"phone": "9111122222"}))
    assert WhatsAppService.resolve_user_phone("user-c") == "919111122222", "a failed lookup must not stick"


def _run_job(monkeypatch, phone):
    sent = []
    monkeypatch.setattr(settings, "WHATSAPP_TEST_RECIPIENT", SHARED_TEST_NUMBER, raising=False)
    monkeypatch.setattr(FirebaseNotificationService, "get_due_reminders_for_user", staticmethod(lambda uid: [dict(ITEM)]))
    monkeypatch.setattr(FirebaseNotificationService, "send_push_notification", staticmethod(lambda **k: {"message": "ok"}))
    monkeypatch.setattr(WhatsAppService, "resolve_user_phone", staticmethod(lambda uid: phone))
    monkeypatch.setattr(WhatsAppService, "send_payment_reminder",
                        staticmethod(lambda **k: sent.append(k["to_phone"]) or {"status": "simulated"}))
    from app.services import notification_log_service
    monkeypatch.setattr(notification_log_service.NotificationLogService, "log_notification",
                        staticmethod(lambda *a, **k: {}))
    result = FirebaseNotificationService._run_daily_payment_reminder_job_for_user("user-d")
    return sent, result


def test_daily_job_sends_to_the_users_own_number_not_the_shared_one(monkeypatch):
    sent, result = _run_job(monkeypatch, "919000011111")
    assert sent == ["919000011111"]
    assert SHARED_TEST_NUMBER not in sent
    assert result["reminders_count"] == 1


def test_daily_job_skips_whatsapp_when_user_has_no_number(monkeypatch):
    sent, result = _run_job(monkeypatch, None)
    assert sent == [], "no number on file: nothing may be sent, in particular not to the shared test number"
    assert result["notifications_sent"][0]["whatsapp_status"] == "skipped"
