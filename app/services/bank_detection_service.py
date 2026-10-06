import calendar
import re
import uuid
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from app.services.transaction_store import TransactionStore, clean_user_id

EMI_KEYWORDS = ["EMI", "INSTALLMENT", "NACH", "ECS", "LOAN", "ACH DEBIT", "FINANCE"]
FRACTION_RE = re.compile(r"(?<!\d)(\d{1,2})\s*/\s*(\d{1,3})(?!\d)")

AMOUNT_TOLERANCE = 0.10
TRIAL_MAX_AMOUNT = 10.0
TRIAL_MIN_CONVERTED_AMOUNT = 100.0
TRIAL_WINDOW_DAYS = 45
PRICE_HIKE_MIN_PCT = 0.10
MONTHLY_GAP_TOLERANCE = 4

CYCLES = {
    "weekly": {"days": 7, "tolerance": 2, "range": (5, 9)},
    "monthly": {"days": 30, "tolerance": MONTHLY_GAP_TOLERANCE, "range": (25, 35)},
    "yearly": {"days": 365, "tolerance": 10, "range": (350, 380)},
}


def _inr(value: float) -> str:
    return f"₹{value:,.0f}"


def _merchant_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()


def _parse_date(value: Any) -> Optional[date]:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _add_months(d: date, n: int) -> date:
    month_index = d.year * 12 + (d.month - 1) + n
    year, month = divmod(month_index, 12)
    month += 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def _step(d: date, frequency: str) -> date:
    if frequency == "weekly":
        return d + timedelta(days=7)
    if frequency == "yearly":
        return _add_months(d, 12)
    return _add_months(d, 1)


def _next_due(last: date, frequency: str, today: date) -> date:
    nxt = _step(last, frequency)
    guard = 0
    while nxt < today and guard < 1000:
        nxt = _step(nxt, frequency)
        guard += 1
    return nxt


def _infer_category(name: str) -> str:
    from app.services.recurring_detector_service import infer_merchant_category
    return infer_merchant_category(name)


def _known(name_key: str, known_keys: Set[str]) -> bool:
    for other in known_keys:
        if name_key == other or (len(other) >= 4 and (other in name_key or name_key in other)):
            return True
    return False


def _classify_cycle(gaps: List[int]) -> Optional[str]:
    avg_gap = sum(gaps) / len(gaps)
    for frequency, spec in CYCLES.items():
        low, high = spec["range"]
        if low <= avg_gap <= high and all(abs(g - spec["days"]) <= spec["tolerance"] for g in gaps):
            return frequency
    return None


def _confidence(amounts: List[float], gaps: List[int], frequency: str) -> int:
    mean_amount = sum(amounts) / len(amounts)
    spread = (max(amounts) - min(amounts)) / mean_amount if mean_amount else 1
    amount_score = max(0.0, 1.0 - spread)
    tolerance = CYCLES[frequency]["tolerance"]
    gap_dev = max(abs(g - CYCLES[frequency]["days"]) for g in gaps) if gaps else 0
    date_score = max(0.0, 1.0 - gap_dev / (tolerance * 2))
    data_score = min(1.0, (len(amounts) - 1) / 4)
    return max(50, min(99, int(round((0.35 * amount_score + 0.35 * date_score + 0.30 * data_score) * 100))))


def _split_price_levels(amounts: List[float]) -> List[List[int]]:
    """Group consecutive payments into levels; a new level starts when the amount moves >10% away."""
    levels: List[List[int]] = []
    for i, amt in enumerate(amounts):
        if levels:
            level_mean = sum(amounts[j] for j in levels[-1]) / len(levels[-1])
            if abs(amt - level_mean) / level_mean <= AMOUNT_TOLERANCE:
                levels[-1].append(i)
                continue
        levels.append([i])
    return levels


def _analyze_emi(name: str, key: str, txs: List[dict], today: date) -> Optional[Dict[str, Any]]:
    if len(txs) < 2:
        return None
    amounts = [t["amount"] for t in txs]
    mean_amount = sum(amounts) / len(amounts)
    if max(abs(a - mean_amount) for a in amounts) / mean_amount > AMOUNT_TOLERANCE:
        return None
    dates = [t["date"] for t in txs]
    gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
    if _classify_cycle(gaps) != "monthly":
        return None
    if (today - dates[-1]).days > 65:
        return None

    paid, total = len(txs), None
    for t in reversed(txs):
        m = FRACTION_RE.search(t["narration"])
        if m and 1 <= int(m.group(1)) <= int(m.group(2)):
            paid, total = int(m.group(1)), int(m.group(2))
            break
    if total is not None and paid >= total:
        return None

    amount = round(mean_amount, 2)
    if total:
        reason = f"{len(txs)} monthly debits of about {_inr(amount)}; the bank narration says installment {paid} of {total}."
    else:
        reason = f"{len(txs)} monthly debits of about {_inr(amount)} that look like a loan EMI. The total number of installments is not in the narration, so please enter it."
    return {
        "kind": "emi",
        "merchant_key": key,
        "merchant_name": name,
        "amount": amount,
        "billing_frequency": "monthly",
        "next_date": _next_due(dates[-1], "monthly", today).isoformat(),
        "confidence": _confidence(amounts, gaps, "monthly"),
        "flags": [],
        "details": {
            "installments_paid": paid,
            "total_installments": total,
            "needs_total": total is None,
            "first_date": dates[0].isoformat(),
            "last_date": dates[-1].isoformat(),
            "txn_count": len(txs),
            "reason": reason,
            "tags": [],
        },
    }


def _analyze_subscription(name: str, key: str, txs: List[dict], today: date) -> Optional[Dict[str, Any]]:
    flags: List[str] = []
    tags: List[str] = []
    details: Dict[str, Any] = {}

    # 1-rupee trial: tiny first debit, then a real price within 45 days
    trial_txs = []
    rest = list(txs)
    while rest and rest[0]["amount"] < TRIAL_MAX_AMOUNT:
        later = [t for t in rest[1:] if t["amount"] >= TRIAL_MIN_CONVERTED_AMOUNT
                 and 0 < (t["date"] - rest[0]["date"]).days <= TRIAL_WINDOW_DAYS]
        if not later:
            break
        trial_txs.append(rest.pop(0))
    if trial_txs:
        converted = rest[0]
        flags.append("trial_converted")
        details["trial_amount"] = trial_txs[0]["amount"]
        details["converted_amount"] = converted["amount"]
        details["trial_date"] = trial_txs[0]["date"].isoformat()
        tags.append(f"Low-cost trial ({_inr(trial_txs[0]['amount'])}) converted to {_inr(converted['amount'])}")

    min_payments = 2 if trial_txs else 3
    if len(rest) < min_payments:
        return None

    amounts = [t["amount"] for t in rest]
    dates = [t["date"] for t in rest]
    levels = _split_price_levels(amounts)
    if len(levels) > 2:
        return None
    if len(levels) == 2 and len(levels[0]) < 2:
        return None

    gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
    frequency = _classify_cycle(gaps)
    if not frequency:
        return None
    if (today - dates[-1]).days > 2 * CYCLES[frequency]["days"]:
        return None

    current = [amounts[i] for i in levels[-1]]
    current_amount = round(sum(current) / len(current), 2)
    if len(levels) == 2:
        old_amount = sum(amounts[i] for i in levels[0]) / len(levels[0])
        if current_amount >= old_amount * (1 + PRICE_HIKE_MIN_PCT):
            pct = round((current_amount - old_amount) / old_amount * 100)
            flags.append("price_hike")
            details["old_amount"] = round(old_amount, 2)
            details["new_amount"] = current_amount
            details["hike_percent"] = pct
            details["hike_since"] = dates[levels[-1][0]].isoformat()
            tags.append(f"Price increased {_inr(old_amount)} to {_inr(current_amount)} (+{pct}%)")

    reason = f"{len(rest)} payments, about {_inr(current_amount)} {frequency}."
    details.update({
        "first_date": dates[0].isoformat(),
        "last_date": dates[-1].isoformat(),
        "txn_count": len(rest),
        "reason": reason,
        "tags": tags,
        "category": _infer_category(name),
    })
    return {
        "kind": "subscription",
        "merchant_key": key,
        "merchant_name": name,
        "amount": current_amount,
        "billing_frequency": frequency,
        "next_date": _next_due(dates[-1], frequency, today).isoformat(),
        "confidence": _confidence(current if len(levels) == 2 else amounts, gaps, frequency),
        "flags": flags,
        "details": details,
    }


def analyze_transactions(
    transactions: List[dict],
    today: Optional[date] = None,
    known_subscriptions: Optional[Set[str]] = None,
    known_emis: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    """Find subscriptions and EMIs in a list of bank debits. Pure function: no database access."""
    today = today or date.today()
    known_subscriptions = known_subscriptions or set()
    known_emis = known_emis or set()

    groups: Dict[str, List[dict]] = {}
    for raw in transactions:
        d = _parse_date(raw.get("transaction_date"))
        try:
            amount = float(raw.get("amount") or 0)
        except (TypeError, ValueError):
            continue
        name = str(raw.get("merchant_name") or "").strip()
        if not d or amount <= 0 or not name:
            continue
        groups.setdefault(_merchant_key(name), []).append(
            {"date": d, "amount": amount, "name": name, "narration": str(raw.get("narration") or "")}
        )

    items: List[Dict[str, Any]] = []
    for key, txs in groups.items():
        if len(txs) < 2:
            continue
        txs.sort(key=lambda t: t["date"])
        display = Counter(t["name"] for t in txs).most_common(1)[0][0]
        text = " ".join(f"{t['narration']} {t['name']}" for t in txs).upper()
        is_emi = any(kw in text for kw in EMI_KEYWORDS)

        item = _analyze_emi(display, key, txs, today) if is_emi else _analyze_subscription(display, key, txs, today)
        if not item:
            continue
        if item["kind"] == "emi" and _known(key, known_emis):
            continue
        if item["kind"] == "subscription" and _known(key, known_subscriptions):
            continue
        items.append(item)

    items.sort(key=lambda i: (i["kind"], i["merchant_name"].lower()))
    return items


class BankDetectionService:
    @staticmethod
    def run(user_id: Any) -> Dict[str, int]:
        """Detect payments from stored transactions and refresh the user's pending review list."""
        from app.core.security import get_supabase_client
        from app.services.subscription_service import SubscriptionService
        from app.services.emi_service import EMIService

        uid = clean_user_id(user_id)
        if not uid:
            return {"pending": 0, "new": 0}

        txns = TransactionStore.get_user_transactions(uid)
        known_subs = {_merchant_key(s.get("merchant_name") or s.get("name") or "")
                      for s in SubscriptionService.get_user_subscriptions(uid)} - {""}
        known_emis = {_merchant_key(e.get("loan_name") or "")
                      for e in EMIService.get_user_emis(uid)} - {""}
        found = analyze_transactions(txns, known_subscriptions=known_subs, known_emis=known_emis)

        supabase = get_supabase_client()
        existing = supabase.from_("detected_items").select("id,kind,merchant_key,status").eq("user_id", uid).execute().data or []
        by_key = {(r["kind"], r["merchant_key"]): r for r in existing}

        now = datetime.now(timezone.utc).isoformat()
        new_count = 0
        found_keys = set()
        for item in found:
            k = (item["kind"], item["merchant_key"])
            found_keys.add(k)
            row = by_key.get(k)
            payload = {**item, "updated_at": now}
            if row is None:
                supabase.from_("detected_items").insert({"id": str(uuid.uuid4()), "user_id": uid, "status": "pending", **payload}).execute()
                new_count += 1
            elif row["status"] == "pending":
                supabase.from_("detected_items").update(payload).eq("id", row["id"]).execute()

        stale = [r["id"] for r in existing if r["status"] == "pending" and (r["kind"], r["merchant_key"]) not in found_keys]
        if stale:
            supabase.from_("detected_items").delete().in_("id", stale).execute()

        pending = supabase.from_("detected_items").select("id", count="exact").eq("user_id", uid).eq("status", "pending").limit(1).execute()
        return {"pending": pending.count or 0, "new": new_count}
