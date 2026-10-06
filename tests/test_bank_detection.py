from datetime import date, timedelta

from app.services.demo_bank_service import build_demo_transactions
from app.services.bank_detection_service import analyze_transactions

TODAY = date(2026, 10, 6)


def _txn(merchant, when, amount, narration=""):
    return {"merchant_name": merchant, "transaction_date": when.isoformat(), "amount": amount, "narration": narration}


def _by_name(items):
    return {i["merchant_name"]: i for i in items}


def test_demo_schedule_is_deterministic_and_only_up_to_today():
    first = build_demo_transactions(TODAY)
    second = build_demo_transactions(TODAY)
    assert first == second
    assert all(r["transaction_date"] <= TODAY.isoformat() for r in first)
    ids = [r["external_id"] for r in first]
    assert len(ids) == len(set(ids)), "external_id must be unique so re-syncing never duplicates"


def test_next_day_only_adds_newly_due_transactions():
    today_ids = {r["external_id"] for r in build_demo_transactions(TODAY)}
    later_ids = {r["external_id"] for r in build_demo_transactions(date(2026, 10, 20))}
    assert today_ids <= later_ids
    added = later_ids - today_ids
    assert "demo:hdfc-loan:2026-10-09" in added
    assert "demo:adobe:2026-10-14" in added


def test_demo_data_produces_expected_review_items():
    items = _by_name(analyze_transactions(build_demo_transactions(TODAY), today=TODAY))

    for name in ("Netflix", "Spotify", "Hotstar", "Adobe Creative Cloud", "Room Rent"):
        assert items[name]["kind"] == "subscription", name
    assert items["Netflix"]["amount"] == 649
    assert items["Netflix"]["billing_frequency"] == "monthly"

    assert "trial_converted" in items["Hotstar"]["flags"]
    assert items["Hotstar"]["details"]["trial_amount"] == 1
    assert items["Hotstar"]["amount"] == 499

    assert "price_hike" in items["Adobe Creative Cloud"]["flags"]
    assert items["Adobe Creative Cloud"]["details"]["old_amount"] == 2499
    assert items["Adobe Creative Cloud"]["details"]["new_amount"] == 3299

    bajaj = items["Bajaj Finserv EMI"]
    assert bajaj["kind"] == "emi"
    assert bajaj["details"]["total_installments"] == 12
    assert bajaj["details"]["installments_paid"] >= 5
    assert not bajaj["details"]["needs_total"]

    hdfc = items["HDFC Bank Loan"]
    assert hdfc["kind"] == "emi"
    assert hdfc["details"]["needs_total"] is True

    everyday = {"Swiggy", "Zomato", "HPCL Petrol Pump", "Local Grocery Store", "Uber India"}
    assert not (everyday & set(items)), "everyday spending must not be flagged as recurring"


def test_next_dates_are_in_the_future():
    for item in analyze_transactions(build_demo_transactions(TODAY), today=TODAY):
        assert item["next_date"] >= TODAY.isoformat(), item["merchant_name"]


def test_old_series_are_ignored_as_ended():
    txs = [_txn("Old Gym", date(2021, 1, 5) + timedelta(days=30 * i), 999) for i in range(5)]
    assert analyze_transactions(txs, today=TODAY) == []


def test_two_payments_are_not_enough_for_a_subscription():
    txs = [_txn("OneOff", date(2026, 8, 5), 300), _txn("OneOff", date(2026, 9, 5), 300)]
    assert analyze_transactions(txs, today=TODAY) == []


def test_varying_bill_amounts_are_not_a_subscription():
    amounts = [1200, 2400, 800, 3100]
    txs = [_txn("Power Co", date(2026, 6, 10) + timedelta(days=30 * i), a) for i, a in enumerate(amounts)]
    assert analyze_transactions(txs, today=TODAY) == []


def test_completed_emi_is_not_suggested():
    txs = [_txn("Phone EMI", date(2026, 8, 2), 1000, "ACH DEBIT 11/12 - PHONE EMI"),
           _txn("Phone EMI", date(2026, 9, 2), 1000, "ACH DEBIT 12/12 - PHONE EMI")]
    assert analyze_transactions(txs, today=TODAY) == []


def test_already_tracked_items_are_skipped():
    items = analyze_transactions(
        build_demo_transactions(TODAY), today=TODAY,
        known_subscriptions={"netflix premium"}, known_emis={"bajaj finserv emi"},
    )
    names = {i["merchant_name"] for i in items}
    assert "Netflix" not in names
    assert "Bajaj Finserv EMI" not in names
    assert "Spotify" in names


def test_small_price_change_is_not_a_hike():
    amounts = [499, 499, 499, 519]
    txs = [_txn("Magazine", date(2026, 6, 20) + timedelta(days=30 * i), a) for i, a in enumerate(amounts)]
    items = analyze_transactions(txs, today=TODAY)
    assert items and "price_hike" not in items[0]["flags"]
