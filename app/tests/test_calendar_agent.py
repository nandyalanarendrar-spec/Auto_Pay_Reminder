import pytest
from datetime import date
from app.services.calendar_agent_service import CalendarAgentService
from app.services.google_calendar_service import GoogleCalendarService

def test_calendar_agent_create_subscription():
    sub_data = {
        "id": "sub_test_101",
        "merchant_name": "Netflix",
        "amount": 649.0,
        "billing_frequency": "Monthly",
        "next_payment_date": "2026-10-01",
        "status": "active",
        "autopay_enabled": True
    }
    res = CalendarAgentService.handle_command({
        "action": "CREATE_CALENDAR_EVENT",
        "type": "SUBSCRIPTION",
        "user_id": "test_user_001",
        "payload": sub_data
    })
    assert res["status"] == "SUCCESS"
    assert "calendar_event_id" in res

def test_calendar_agent_update_subscription():
    sub_data = {
        "id": "sub_test_101",
        "calendar_event_id": "sim-evt-test-123",
        "merchant_name": "Netflix",
        "amount": 799.0,
        "billing_frequency": "Monthly",
        "next_payment_date": "2026-10-05",
        "status": "active",
        "autopay_enabled": True
    }
    res = CalendarAgentService.handle_command({
        "action": "UPDATE_CALENDAR_EVENT",
        "type": "SUBSCRIPTION",
        "user_id": "test_user_001",
        "payload": sub_data
    })
    assert res["status"] == "SUCCESS"

def test_calendar_agent_delete_subscription():
    sub_data = {
        "id": "sub_test_101",
        "calendar_event_id": "sim-evt-test-123",
        "merchant_name": "Netflix",
        "amount": 649.0,
        "status": "cancelled",
        "autopay_enabled": False
    }
    res = CalendarAgentService.handle_command({
        "action": "DELETE_CALENDAR_EVENT",
        "type": "SUBSCRIPTION",
        "user_id": "test_user_001",
        "payload": sub_data
    })
    assert res["status"] == "SUCCESS"
    assert res["calendar_event_id"] is None

def test_calendar_agent_create_emi():
    emi_data = {
        "id": "emi_test_101",
        "loan_name": "Laptop Loan EMI",
        "installment_amount": 3500.0,
        "next_due_date": "2026-10-15",
        "installments_paid": 2,
        "total_installments": 12,
        "status": "active"
    }
    res = CalendarAgentService.handle_command({
        "action": "CREATE_CALENDAR_EVENT",
        "type": "EMI",
        "user_id": "test_user_001",
        "payload": emi_data
    })
    assert res["status"] == "SUCCESS"
    assert "calendar_event_id" in res

def test_calendar_resync_all():
    res = CalendarAgentService.resync_user_calendar("test_user_001")
    assert res["success"] is True
    assert "synced_subscriptions" in res
