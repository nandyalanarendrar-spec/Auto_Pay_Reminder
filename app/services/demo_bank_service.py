import calendar
import hashlib
import uuid
from datetime import date
from typing import Any, Dict, List, Optional

from app.services.transaction_store import TransactionStore, SOURCE_DEMO, clean_user_id

HISTORY_MONTHS = 6
DEMO_ACCOUNT = "demo-account-XXXX4821"

NOISE_MERCHANTS = ["Swiggy", "Zomato", "HPCL Petrol Pump", "Local Grocery Store", "Uber India"]


def _add_months(d: date, n: int) -> date:
    month_index = d.year * 12 + (d.month - 1) + n
    year, month = divmod(month_index, 12)
    month += 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def _month_day(today: date, month_offset: int, day: int) -> date:
    first = _add_months(date(today.year, today.month, 1), month_offset)
    return date(first.year, first.month, min(day, calendar.monthrange(first.year, first.month)[1]))


def _digits(*parts: str, length: int = 12) -> str:
    h = hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()
    return str(int(h, 16))[:length].rjust(length, "0")


def _row(key: str, when: date, merchant: str, amount: float, narration: str, mode: str) -> Dict[str, Any]:
    return {
        "external_id": f"demo:{key}:{when.isoformat()}",
        "merchant_name": merchant,
        "amount": float(amount),
        "transaction_date": when.isoformat(),
        "narration": narration,
        "mode": mode,
    }


def build_demo_transactions(today: Optional[date] = None, months: int = HISTORY_MONTHS) -> List[Dict[str, Any]]:
    """
    Deterministic fake bank history ending today. The same date always yields the same external_id, so
    running this daily only ever adds the transactions that have newly come due.
    """
    today = today or date.today()
    start = _month_day(today, -(months - 1), 1)
    rows: List[Dict[str, Any]] = []

    def monthly(key, merchant, day, amount_for, narration_for, mode="UPI", first_offset=-(months - 1)):
        for offset in range(first_offset, 1):
            when = _month_day(today, offset, day)
            if start <= when <= today:
                idx = offset - first_offset
                rows.append(_row(key, when, merchant, amount_for(idx), narration_for(when, idx), mode))

    monthly("netflix", "Netflix", 5, lambda i: 649,
            lambda w, i: f"UPI/{_digits('netflix', w.isoformat())}/NETFLIX COM/netflix@icici/AutoPay")
    monthly("spotify", "Spotify", 11, lambda i: 179,
            lambda w, i: f"UPI/{_digits('spotify', w.isoformat())}/SPOTIFY INDIA/spotify@hdfcbank/AutoPay")

    # 1-rupee trial, then the full price a week later and every month after
    trial_day = _month_day(today, -4, 20)
    if start <= trial_day <= today:
        rows.append(_row("hotstar-trial", trial_day, "Hotstar", 1,
                         f"UPI/{_digits('hotstar-trial', trial_day.isoformat())}/HOTSTAR/hotstar@icici/Trial Mandate", "UPI"))
    monthly("hotstar", "Hotstar", 27, lambda i: 499,
            lambda w, i: f"UPI/{_digits('hotstar', w.isoformat())}/HOTSTAR/hotstar@icici/AutoPay",
            first_offset=-4)

    # Price hike: 2499 for three months, then 3299
    monthly("adobe", "Adobe Creative Cloud", 14, lambda i: 2499 if i < 3 else 3299,
            lambda w, i: f"UPI/{_digits('adobe', w.isoformat())}/ADOBE SYSTEMS/adobe@axis/AutoPay")

    # EMI with an installment counter in the narration (starts at 3/12)
    monthly("bajaj-emi", "Bajaj Finserv EMI", 2, lambda i: 2200,
            lambda w, i: f"ACH DEBIT {min(12, 3 + i)}/12 - BAJAJ FINSERV EMI", mode="NACH")

    # EMI with no installment counter: the user has to supply the total
    monthly("hdfc-loan", "HDFC Bank Loan", 9, lambda i: 6500,
            lambda w, i: "NACH DEBIT - HDFC BANK LOAN EMI", mode="NACH")

    # Not a subscription, but it repeats monthly: a good case for the Ignore button
    monthly("rent", "Room Rent", 1, lambda i: 12000,
            lambda w, i: f"UPI/{_digits('rent', w.isoformat())}/RAJESH KUMAR/rajesh@ybl/Monthly rent")

    # Everyday spending that must NOT look recurring
    day = start
    while day <= today:
        h = int(_digits("noise", day.isoformat(), length=8))
        if h % 5 == 0:
            merchant = NOISE_MERCHANTS[h % len(NOISE_MERCHANTS)]
            amount = 80 + (h // 7) % 820
            rows.append(_row(f"noise-{h % 97}", day, merchant, amount,
                             f"UPI/{_digits('noise', day.isoformat())}/{merchant.upper()}", "UPI"))
        day = date.fromordinal(day.toordinal() + 1)

    rows.sort(key=lambda r: r["transaction_date"])
    return rows


class DemoBankService:
    @staticmethod
    def _to_db_rows(user_id: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "is_labeled_recurring": False,
                "is_labeled_emi": False,
                "source": SOURCE_DEMO,
                "account_ref": DEMO_ACCOUNT,
                **r,
            }
            for r in rows
        ]

    @staticmethod
    def sync(user_id: Any, today: Optional[date] = None) -> int:
        """Add every demo transaction that has come due and is not stored yet. Safe to call repeatedly."""
        uid = clean_user_id(user_id)
        if not uid:
            return 0
        return TransactionStore.insert_many(DemoBankService._to_db_rows(uid, build_demo_transactions(today)))

    @staticmethod
    def remove(user_id: Any) -> int:
        return TransactionStore.delete_by_source(user_id, SOURCE_DEMO)

    @staticmethod
    def is_loaded(user_id: Any) -> bool:
        return TransactionStore.count_by_source(user_id, SOURCE_DEMO) > 0

    @staticmethod
    def run_daily_for_all() -> Dict[str, int]:
        """Called by the scheduler: top up demo data and re-run detection for users who loaded the demo."""
        from app.services.bank_detection_service import BankDetectionService
        users = TransactionStore.user_ids_with_source(SOURCE_DEMO)
        added_total = 0
        for uid in users:
            try:
                added_total += DemoBankService.sync(uid)
                BankDetectionService.run(uid)
            except Exception as err:
                print(f"Demo bank daily update failed for {uid}: {err}")
        return {"users": len(users), "transactions_added": added_total}
