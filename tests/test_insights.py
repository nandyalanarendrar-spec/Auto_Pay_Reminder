"""Spending summary, price-hike/trial alerts and the assistant's transaction answers."""
import os
import sys
import uuid
from datetime import date

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ai_service import SpendingTransactionsAgent
from app.services.insight_alert_service import ALERT_SENT_DATE, InsightAlertService, build_alerts
from app.services.spending_insights_service import SpendingInsightsService, summarize

TODAY = date(2026, 10, 15)


def _t(merchant, when, amount, source="manual"):
    return {"merchant_name": merchant, "transaction_date": when, "amount": amount, "source": source}


SAMPLE = [
    _t("Netflix", "2026-10-05", 649),
    _t("Swiggy", "2026-10-09", 351),
    _t("Netflix", "2026-09-05", 649),
    _t("Swiggy", "2026-09-20", 500),
    _t("Rent", "2026-08-01", 12000),
    _t("Old shop", "2025-01-01", 999),      # outside the 6 month window
    _t("Refund", "2026-10-10", -200),       # not spending
    _t("Broken", "not-a-date", 50),
    _t("netflix", "2026-07-05", 649),       # same merchant, different case
]


# --------------------------------------------------------------------------- summary

def test_summary_totals_and_change():
    s = summarize(SAMPLE, today=TODAY, months=6)
    assert [m["month"] for m in s["months"]] == ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]
    assert s["this_month"]["total"] == 1000 and s["this_month"]["count"] == 2
    assert s["last_month"]["total"] == 1149
    assert s["change_pct"] == pytest.approx(-13.0, abs=0.1)
    assert s["transaction_count"] == 6, "old, negative and unreadable rows must be ignored"
    assert s["has_data"] is True


def test_top_merchants_group_case_insensitively():
    s = summarize(SAMPLE, today=TODAY, months=6)
    top = s["top_merchants"]
    assert top[0]["name"] == "Rent" and top[0]["total"] == 12000
    netflix = next(m for m in top if m["name"].lower() == "netflix")
    assert netflix["total"] == 649 * 3 and netflix["count"] == 3
    assert sum(m["share_pct"] for m in summarize(SAMPLE, today=TODAY, top=10)["top_merchants"]) == pytest.approx(100, abs=0.5)


def test_empty_data_is_handled():
    s = summarize([], today=TODAY)
    assert s["has_data"] is False and s["change_pct"] is None and s["top_merchants"] == []
    assert "No bank" in SpendingInsightsService.describe(s)


def test_month_window_crosses_year_boundary():
    s = summarize([_t("A", "2025-12-20", 100), _t("A", "2026-01-03", 50)], today=date(2026, 2, 10), months=3)
    assert [m["month"] for m in s["months"]] == ["2025-12", "2026-01", "2026-02"]
    assert s["months"][0]["total"] == 100 and s["months"][1]["total"] == 50


# --------------------------------------------------------------------------- alerts

def test_alerts_for_price_hike_and_trial():
    items = [
        {"id": "a", "kind": "subscription", "merchant_name": "Adobe", "amount": 3299, "status": "pending",
         "flags": ["price_hike"], "details": {"old_amount": 2499, "new_amount": 3299}},
        {"id": "b", "kind": "subscription", "merchant_name": "Hotstar", "amount": 499, "status": "pending",
         "flags": ["trial_converted"], "details": {"trial_amount": 1}},
        {"id": "c", "kind": "subscription", "merchant_name": "Netflix", "amount": 649, "status": "pending", "flags": []},
        {"id": "d", "kind": "subscription", "merchant_name": "Ignored", "amount": 10, "status": "ignored",
         "flags": ["price_hike"], "details": {"old_amount": 5, "new_amount": 10}},
    ]
    alerts = build_alerts(items)
    kinds = {(a["merchant_name"], a["kind"]) for a in alerts}
    assert kinds == {("Adobe", "price_hike"), ("Hotstar", "trial_converted")}
    adobe = next(a for a in alerts if a["kind"] == "price_hike")
    assert "₹3,299" in adobe["message"] and "₹2,499" in adobe["message"] and "₹9,600" in adobe["message"]
    hotstar = next(a for a in alerts if a["kind"] == "trial_converted")
    assert "₹499" in hotstar["message"] and "₹1" in hotstar["message"]


def test_alert_builder_survives_missing_details():
    alerts = build_alerts([{"id": "x", "merchant_name": "Odd", "amount": 100, "flags": ["price_hike"], "details": None}])
    assert len(alerts) == 1 and "Odd" in alerts[0]["title"]


# --------------------------------------------------------------------------- assistant

SUMMARY = summarize(SAMPLE, today=TODAY, months=6)


def test_assistant_answers_this_month_from_real_numbers():
    reply = SpendingTransactionsAgent.process("How much did I spend this month?", SUMMARY)
    assert "₹1,000.00" in reply and "13.0% less" in reply


def test_assistant_answers_last_month_and_top_merchants():
    assert "₹1,149.00" in SpendingTransactionsAgent.process("what did I spend last month", SUMMARY)
    top = SpendingTransactionsAgent.process("where did my money go", SUMMARY)
    assert "Rent" in top and top.index("Rent") < top.index("Swiggy")


def test_assistant_leaves_plan_questions_to_other_agents():
    assert SpendingTransactionsAgent.process("how many subscriptions do I have", SUMMARY) is None
    assert SpendingTransactionsAgent.process("when is my next EMI", SUMMARY) is None
    assert SpendingTransactionsAgent.process("hello", SUMMARY) is None


def test_assistant_is_honest_when_there_is_no_data():
    reply = SpendingTransactionsAgent.process("how much did I spend this month", {"has_data": False})
    assert "do not see any transactions" in reply


def test_assistant_understands_telugu_keywords():
    assert "₹1,000.00" in SpendingTransactionsAgent.process("ఈ నెల ఖర్చు ఎంత", SUMMARY)


# --------------------------------------------------------------------------- live database flow

@pytest.fixture(scope="module")
def user():
    from app.core.security import get_supabase_client

    supabase = get_supabase_client()
    email = f"pytest_insight_{uuid.uuid4().hex[:8]}@example.com"
    res = supabase.auth.sign_up({"email": email, "password": "SecurePassword123!"})
    uid = str(res.user.id)
    yield {"id": uid}
    for table in ("notification_logs", "detected_items", "transactions", "subscriptions", "emis"):
        try:
            supabase.from_(table).delete().eq("user_id", uid).execute()
        except Exception:
            pass


def test_db_flow_alerts_are_sent_once_and_spending_matches(user):
    from app.services.bank_detection_service import BankDetectionService
    from app.services.demo_bank_service import DemoBankService

    uid = user["id"]
    DemoBankService.sync(uid)
    BankDetectionService.run(uid)  # also sends the alerts once

    alerts = InsightAlertService.get_alerts(uid)
    kinds = {(a["merchant_name"], a["kind"]) for a in alerts}
    assert ("Hotstar", "trial_converted") in kinds
    assert ("Adobe Creative Cloud", "price_hike") in kinds

    assert InsightAlertService.notify_new(uid) == 0, "already sent by the detection run; must not repeat"

    summary = SpendingInsightsService.build(uid)
    assert summary["has_data"] and len(summary["months"]) == 6
    assert summary["transaction_count"] > 50
    assert any(m["name"] for m in summary["top_merchants"])
