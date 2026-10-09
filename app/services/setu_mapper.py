import hashlib
import re
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Tuple

from app.services.transaction_store import SOURCE_SETU

_WORDS_TO_SKIP = {
    "UPI", "NEFT", "IMPS", "RTGS", "ACH", "NACH", "POS", "ECS", "ATM", "DEBIT", "CREDIT", "PAYMENT",
    "TO", "FROM", "TRANSFER", "TXN", "REF", "AUTOPAY", "MANDATE", "BANK", "DR", "CR", "PUR",
    "CASH", "CARD", "CHEQUE", "CHQ", "FT", "DE", "OTHERS", "TFR", "TRF", "CLG", "SELF",
}
_TRAILING_NOISE = {"COM", "PVT", "LTD", "LIMITED", "PRIVATE"}


def extract_merchant(narration: Optional[str]) -> str:
    """Best-effort merchant name from a bank narration such as 'UPI/123456/NETFLIX COM/netflix@icici/AutoPay'."""
    text = (narration or "").strip()
    if not text:
        return "Unknown"

    def clean_words(chunk: str) -> List[str]:
        letters = re.sub(r"[^A-Za-z ]", " ", chunk)
        return [w for w in letters.split() if len(w) > 2 and w.upper() not in _WORDS_TO_SKIP]

    for part in re.split(r"[/|:\-]+", text):
        part = part.strip()
        if not part or "@" in part:
            continue
        words = clean_words(part)
        while words and words[-1].upper() in _TRAILING_NOISE and len(words) > 1:
            words.pop()
        if words:
            return " ".join(w.capitalize() for w in words[:3])

    words = clean_words(text)
    return " ".join(w.capitalize() for w in words[:3]) if words else "Unknown"


def _lower_keys(d: Any) -> Dict[str, Any]:
    return {str(k).lower(): v for k, v in d.items()} if isinstance(d, dict) else {}


def _iter_accounts(session_json: Dict[str, Any]) -> Iterator[Tuple[str, List[dict]]]:
    """Yield (masked account number, transaction dicts) for every account in a Setu FI data response."""
    for fip in session_json.get("fips") or []:
        for account in (_lower_keys(fip).get("accounts") or []):
            acc = _lower_keys(account)
            masked = str(acc.get("maskedaccnumber") or acc.get("maskedaccountnumber") or "account")
            data = _lower_keys(acc.get("data"))
            body = _lower_keys(data.get("account"))
            tx_block = body.get("transactions")
            if isinstance(tx_block, dict):
                tx_block = _lower_keys(tx_block).get("transaction")
            txs = [t for t in (tx_block or []) if isinstance(t, dict)]
            yield masked, txs


def _parse_date(raw: Any) -> Optional[str]:
    if not raw:
        return None
    text = str(raw)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return text[:10] if re.match(r"\d{4}-\d{2}-\d{2}", text) else None


def to_transaction_rows(session_json: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
    """Convert Setu FI data into our transactions rows. Only money going out is kept."""
    rows: List[Dict[str, Any]] = []
    for masked, txs in _iter_accounts(session_json):
        for raw in txs:
            tx = _lower_keys(raw)
            if str(tx.get("type", "")).upper() != "DEBIT":
                continue
            try:
                amount = float(tx.get("amount"))
            except (TypeError, ValueError):
                continue
            when = _parse_date(tx.get("transactiontimestamp")) or _parse_date(tx.get("valuedate"))
            if amount <= 0 or not when:
                continue
            narration = str(tx.get("narration") or "")
            txn_id = str(tx.get("txnid") or "").strip()
            if not txn_id:
                txn_id = hashlib.sha1(
                    f"{tx.get('transactiontimestamp')}|{amount}|{narration}|{tx.get('currentbalance')}".encode()
                ).hexdigest()[:20]
            rows.append({
                "user_id": user_id,
                "merchant_name": extract_merchant(narration),
                "amount": amount,
                "transaction_date": when,
                "narration": narration,
                "mode": str(tx.get("mode") or "OTHERS"),
                "is_labeled_recurring": False,
                "is_labeled_emi": False,
                "source": SOURCE_SETU,
                "external_id": f"setu:{masked}:{txn_id}",
                "account_ref": masked,
            })
    return rows
