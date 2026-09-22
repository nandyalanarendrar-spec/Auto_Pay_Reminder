import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

AUDIT_LOGS_FILE = "audit_logs.json"

def _load_audit_logs() -> List[Dict[str, Any]]:
    if os.path.exists(AUDIT_LOGS_FILE):
        try:
            with open(AUDIT_LOGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading audit logs:", e)
            return []
    return []

def _save_audit_logs(logs: List[Dict[str, Any]]):
    try:
        with open(AUDIT_LOGS_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print("Error saving audit logs:", e)

class AuditLoggerService:

    @staticmethod
    def log_action(
        user_id: str,
        action: str,
        ip_address: Optional[str] = "127.0.0.1",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Records an audit log entry for sensitive user actions.
        """
        clean_uid = str(user_id).strip('"\'')
        log_entry = {
            "id": f"audit-{uuid.uuid4().hex[:10]}",
            "user_id": clean_uid,
            "action": action,
            "ip_address": ip_address or "127.0.0.1",
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        logs = _load_audit_logs()
        logs.append(log_entry)
        _save_audit_logs(logs)
        return log_entry

    @staticmethod
    def get_user_logs(user_id: str) -> List[Dict[str, Any]]:
        clean_uid = str(user_id).strip('"\'')
        logs = _load_audit_logs()
        user_logs = [l for l in logs if l.get("user_id") == clean_uid]
        return sorted(user_logs, key=lambda x: x.get("timestamp", ""), reverse=True)
