"""Monthly spending summary built from the user's stored transactions (manual, demo and bank-imported)."""
from collections import defaultdict
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional

from app.services.transaction_store import TransactionStore

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _parse_day(value: Any) -> Optional[date]:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def _amount(row: dict) -> float:
    try:
        return float(row.get("amount") or 0)
    except (ValueError, TypeError):
        return 0.0


def _shift(year: int, month: int, delta: int) -> tuple:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def _month_key(year: int, month: int) -> str:
    return f"{year}-{month:02d}"


def summarize(transactions: Iterable[dict], today: Optional[date] = None, months: int = 6, top: int = 5) -> Dict[str, Any]:
    """Pure function: totals per month for the last `months` months (current month included) and top merchants."""
    today = today or date.today()
    months = max(1, min(int(months or 6), 24))

    window: List[tuple] = [_shift(today.year, today.month, -i) for i in range(months - 1, -1, -1)]
    totals = {_month_key(y, m): {"total": 0.0, "count": 0} for y, m in window}
    merchants: Dict[str, Dict[str, Any]] = {}
    sources: Dict[str, int] = defaultdict(int)
    in_window = 0

    for row in transactions:
        day = _parse_day(row.get("transaction_date"))
        amount = _amount(row)
        if day is None or amount <= 0:
            continue
        key = _month_key(day.year, day.month)
        if key not in totals:
            continue
        in_window += 1
        totals[key]["total"] += amount
        totals[key]["count"] += 1
        sources[str(row.get("source") or "manual")] += 1

        name = str(row.get("merchant_name") or "Unknown").strip() or "Unknown"
        bucket = merchants.setdefault(name.lower(), {"name": name, "total": 0.0, "count": 0})
        bucket["total"] += amount
        bucket["count"] += 1

    month_rows = [
        {
            "month": _month_key(y, m),
            "label": MONTH_NAMES[m - 1],
            "total": round(totals[_month_key(y, m)]["total"], 2),
            "count": totals[_month_key(y, m)]["count"],
        }
        for y, m in window
    ]

    this_month = month_rows[-1]
    last_month = month_rows[-2] if len(month_rows) > 1 else {"month": None, "label": "", "total": 0.0, "count": 0}
    change_pct = None
    if last_month["total"] > 0:
        change_pct = round((this_month["total"] - last_month["total"]) / last_month["total"] * 100, 1)

    # Average over completed months that actually had spending, so a half-finished month does not drag it down.
    completed = [r["total"] for r in month_rows[:-1] if r["total"] > 0]
    average = round(sum(completed) / len(completed), 2) if completed else 0.0

    grand_total = sum(r["total"] for r in month_rows)
    ranked = sorted(merchants.values(), key=lambda b: b["total"], reverse=True)[:top]
    top_merchants = [
        {
            "name": b["name"],
            "total": round(b["total"], 2),
            "count": b["count"],
            "share_pct": round(b["total"] / grand_total * 100, 1) if grand_total else 0.0,
        }
        for b in ranked
    ]

    return {
        "has_data": in_window > 0,
        "months": month_rows,
        "this_month": this_month,
        "last_month": last_month,
        "change_pct": change_pct,
        "average_monthly": average,
        "total_spent": round(grand_total, 2),
        "transaction_count": in_window,
        "top_merchants": top_merchants,
        "sources": dict(sources),
        "window_months": months,
    }


class SpendingInsightsService:
    @staticmethod
    def build(user_id: Any, months: int = 6) -> Dict[str, Any]:
        return summarize(TransactionStore.get_user_transactions(user_id), months=months)

    @staticmethod
    def describe(summary: Dict[str, Any]) -> str:
        """Plain-text recap used as grounded context for the assistant."""
        if not summary.get("has_data"):
            return "No bank or card transactions are stored for this user yet."
        this_m, last_m = summary["this_month"], summary["last_month"]
        lines = [
            f"Spent this month ({this_m['label']}): Rs {this_m['total']:,.2f} over {this_m['count']} payments.",
            f"Spent last month ({last_m['label']}): Rs {last_m['total']:,.2f} over {last_m['count']} payments.",
        ]
        if summary.get("change_pct") is not None:
            lines.append(f"Change versus last month: {summary['change_pct']:+.1f}%.")
        if summary.get("average_monthly"):
            lines.append(f"Average of completed months: Rs {summary['average_monthly']:,.2f}.")
        top = ", ".join(f"{m['name']} Rs {m['total']:,.2f}" for m in summary["top_merchants"][:3])
        if top:
            lines.append(f"Top merchants in the last {summary['window_months']} months: {top}.")
        return " ".join(lines)
