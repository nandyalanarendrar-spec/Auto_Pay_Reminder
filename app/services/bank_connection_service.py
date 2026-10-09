import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.core.security import get_supabase_client
from app.services import setu_aa_service as setu
from app.services.bank_detection_service import BankDetectionService
from app.services.setu_aa_service import SetuError
from app.services.setu_mapper import to_transaction_rows
from app.services.transaction_store import SOURCE_SETU, TransactionStore, clean_user_id

READY_STATUSES = {"COMPLETED", "PARTIAL"}
FAILED_STATUSES = {"FAILED", "EXPIRED", "REJECTED"}
POLL_ATTEMPTS = 12
POLL_SECONDS = 3


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_day(d: datetime) -> str:
    return d.strftime("%Y-%m-%dT00:00:00Z")


def _table():
    return get_supabase_client().from_("bank_consents")


class BankConnectionService:
    @staticmethod
    def validate_mobile(mobile: Any) -> str:
        digits = re.sub(r"\D", "", str(mobile or ""))
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        if not re.fullmatch(r"[6-9]\d{9}", digits):
            raise ValueError("Enter a valid 10-digit Indian mobile number.")
        return digits

    @staticmethod
    def latest(user_id: str) -> Optional[Dict[str, Any]]:
        res = _table().select("*").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        return (res.data or [None])[0]

    @staticmethod
    def connect(user_id: Any, mobile: Any) -> Dict[str, Any]:
        uid = clean_user_id(user_id)
        number = BankConnectionService.validate_mobile(mobile)
        today = datetime.now(timezone.utc)
        data_from, data_to = _iso_day(today - timedelta(days=365)), _iso_day(today)

        created = setu.create_consent(number, data_from, data_to)
        consent_id, url = created.get("id"), created.get("url")
        if not consent_id or not url:
            raise SetuError("Setu did not return a consent link. Please try again.")

        # Only the latest connection matters; drop older attempts that never became active.
        _table().delete().eq("user_id", uid).neq("status", "ACTIVE").execute()
        _table().insert({
            "id": str(uuid.uuid4()),
            "user_id": uid,
            "consent_id": consent_id,
            "status": created.get("status") or "PENDING",
            "consent_url": url,
            "phone_masked": "XXXXXX" + number[-4:],
            "data_from": data_from,
            "data_to": data_to,
        }).execute()
        return {"consent_id": consent_id, "url": url}

    @staticmethod
    def refresh(row: Dict[str, Any]) -> Dict[str, Any]:
        """Pull the current consent status from Setu and store it."""
        remote = setu.get_consent(row["consent_id"])
        accounts = [
            {"masked": a.get("maskedAccNumber"), "type": a.get("accType"), "fip": a.get("fipId")}
            for a in (remote.get("accountsLinked") or [])
        ]
        update = {"status": remote.get("status") or row["status"], "accounts": accounts, "updated_at": _now()}
        _table().update(update).eq("id", row["id"]).execute()
        return {**row, **update}

    @staticmethod
    def status(user_id: Any) -> Dict[str, Any]:
        uid = clean_user_id(user_id)
        base = {"configured": setu.is_configured(), "state": "not_connected"}
        row = BankConnectionService.latest(uid) if uid else None
        if not row:
            return base
        if row["status"] == "PENDING" and base["configured"]:
            try:
                row = BankConnectionService.refresh(row)
            except SetuError as err:
                print("Setu consent refresh note:", err)
        return {
            **base,
            "state": str(row["status"]).lower(),
            "phone_masked": row.get("phone_masked"),
            "accounts": row.get("accounts") or [],
            "last_synced_at": row.get("last_synced_at"),
            "consent_url": row.get("consent_url") if row["status"] == "PENDING" else None,
        }

    @staticmethod
    def sync(user_id: Any) -> Dict[str, Any]:
        uid = clean_user_id(user_id)
        row = BankConnectionService.latest(uid) if uid else None
        if not row:
            raise SetuError("No bank is connected yet.", 404)
        row = BankConnectionService.refresh(row)
        if row["status"] != "ACTIVE":
            raise SetuError(f"The bank connection is {str(row['status']).lower()}, not active yet.", 409)

        try:
            session = setu.create_session(row["consent_id"], _iso_day(_parse(row["data_from"])), _iso_day(_parse(row["data_to"])))
        except SetuError as err:
            if "use exceeded" in str(err).lower():
                raise SetuError("Setu allows one data fetch per day for each bank connection (sandbox limit). Try again tomorrow.", 429)
            raise
        session_id = session.get("id")
        if not session_id:
            raise SetuError("Setu did not start a data session.")
        _table().update({"last_session_id": session_id, "updated_at": _now()}).eq("id", row["id"]).execute()

        data: Dict[str, Any] = {}
        for _ in range(POLL_ATTEMPTS):
            data = setu.get_session(session_id)
            state = str(data.get("status", "")).upper()
            if state in READY_STATUSES:
                break
            if state in FAILED_STATUSES:
                raise SetuError(f"Setu could not prepare the data ({state.lower()}).")
            time.sleep(POLL_SECONDS)
        else:
            raise SetuError("Setu is still preparing your data. Please try Sync again in a minute.", 202)

        rows = to_transaction_rows(data, uid)
        for r in rows:
            r["id"] = str(uuid.uuid4())
        added = TransactionStore.insert_many(rows)
        _table().update({"last_synced_at": _now(), "updated_at": _now()}).eq("id", row["id"]).execute()
        detection = BankDetectionService.run(uid)
        return {"fetched": len(rows), "added": added, "pending_review": detection["pending"], "new_items": detection["new"]}

    @staticmethod
    def disconnect(user_id: Any) -> Dict[str, Any]:
        uid = clean_user_id(user_id)
        rows = _table().select("*").eq("user_id", uid).execute().data or [] if uid else []
        for row in rows:
            try:
                setu.revoke_consent(row["consent_id"])
            except SetuError as err:
                print("Setu revoke note (continuing):", err)
        removed = TransactionStore.delete_by_source(uid, SOURCE_SETU)
        if uid:
            _table().delete().eq("user_id", uid).execute()
        detection = BankDetectionService.run(uid) if uid else {"pending": 0}
        return {"removed_transactions": removed, "pending_review": detection["pending"]}

    @staticmethod
    def _find_ids(payload: Any, keys: set) -> List[str]:
        found: List[str] = []
        if isinstance(payload, dict):
            for k, v in payload.items():
                if str(k).lower() in keys and isinstance(v, str):
                    found.append(v)
                else:
                    found.extend(BankConnectionService._find_ids(v, keys))
        elif isinstance(payload, list):
            for item in payload:
                found.extend(BankConnectionService._find_ids(item, keys))
        return found

    @staticmethod
    def handle_webhook(payload: Any) -> Dict[str, Any]:
        """
        Setu calls this when a consent or data session changes. The payload is never trusted: it is only a
        hint about which connection to re-check, and the real status is always read back from Setu.
        """
        consent_ids = BankConnectionService._find_ids(payload, {"consentid", "consent_id"})
        session_ids = BankConnectionService._find_ids(payload, {"datasessionid", "sessionid", "session_id"})

        rows: List[Dict[str, Any]] = []
        for cid in set(consent_ids):
            rows.extend(_table().select("*").eq("consent_id", cid).execute().data or [])
        for sid in set(session_ids):
            rows.extend(_table().select("*").eq("last_session_id", sid).execute().data or [])

        handled = 0
        seen = set()
        for row in rows:
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            try:
                row = BankConnectionService.refresh(row)
                if row["status"] == "ACTIVE" and not row.get("last_synced_at"):
                    BankConnectionService.sync(row["user_id"])
                handled += 1
            except Exception as err:
                print("Setu webhook handling note:", err)
        return {"handled": handled}

    @staticmethod
    def run_daily_for_all() -> Dict[str, int]:
        rows = _table().select("user_id,last_synced_at").eq("status", "ACTIVE").limit(1000).execute().data or []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=20)
        # Setu allows one fetch per day per connection, so skip anyone already synced recently.
        users = sorted({
            str(r["user_id"]) for r in rows
            if not r.get("last_synced_at") or _parse(r["last_synced_at"]) < cutoff
        })
        synced = 0
        for uid in users:
            try:
                BankConnectionService.sync(uid)
                synced += 1
            except Exception as err:
                print(f"Setu daily sync failed for {uid}: {err}")
        return {"users": len(users), "synced": synced}


def _parse(value: Any) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
