import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from app.core.security import get_supabase_client

# In-memory fallback log cache for cross-thread backend execution when Supabase table isn't migrated
_in_memory_logs: List[Dict[str, Any]] = []

class NotificationLogService:

    @staticmethod
    def is_already_notified(
        user_id: str,
        entity_type: str,
        entity_id: str,
        notification_type: str,
        sent_date: Optional[str] = None
    ) -> bool:
        """
        Checks if a notification for this user, entity, notification_type (7d, 3d, 1d, 0d),
        and sent_date has already been logged.
        """
        clean_uid = str(user_id).strip('"\'')
        clean_eid = str(entity_id).strip('"\'')
        target_date = sent_date or date.today().isoformat()

        # 1. Check Supabase DB
        try:
            supabase = get_supabase_client()
            res = (
                supabase.from_("notification_logs")
                .select("id")
                .eq("user_id", clean_uid)
                .eq("entity_type", entity_type)
                .eq("entity_id", clean_eid)
                .eq("notification_type", notification_type)
                .eq("sent_date", target_date)
                .execute()
            )
            if res.data and len(res.data) > 0:
                return True
        except Exception as err:
            # Fallback to in-memory check
            pass

        # 2. Fallback in-memory check
        for log in _in_memory_logs:
            if (
                log.get("user_id") == clean_uid
                and log.get("entity_type") == entity_type
                and log.get("entity_id") == clean_eid
                and log.get("notification_type") == notification_type
                and log.get("sent_date") == target_date
            ):
                return True

        return False

    @staticmethod
    def log_notification(
        user_id: str,
        entity_type: str,
        entity_id: str,
        notification_type: str,
        sent_date: Optional[str] = None,
        channel: str = "web"
    ) -> Dict[str, Any]:
        """
        Logs a sent notification record into the backend database.
        """
        clean_uid = str(user_id).strip('"\'')
        clean_eid = str(entity_id).strip('"\'')
        target_date = sent_date or date.today().isoformat()
        now_iso = datetime.utcnow().isoformat()

        payload = {
            "user_id": clean_uid,
            "entity_type": entity_type,
            "entity_id": clean_eid,
            "notification_type": notification_type,
            "sent_date": target_date,
            "sent_at": now_iso,
            "channel": channel
        }

        # 1. Thread-safe in-memory cache check
        if not NotificationLogService.is_already_notified(clean_uid, entity_type, clean_eid, notification_type, target_date):
            _in_memory_logs.append(payload)

        # 2. Upsert / Graceful Unique Constraint Handling in Supabase DB
        try:
            supabase = get_supabase_client()
            res = (
                supabase.from_("notification_logs")
                .upsert(
                    payload,
                    on_conflict="user_id,entity_type,entity_id,notification_type,sent_date"
                )
                .execute()
            )
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as err:
            # Handle unique constraint violation (duplicate key) gracefully without throwing 500
            error_msg = str(err)
            if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower() or "23505" in error_msg:
                print(f"ℹ️ Notification already logged by concurrent worker: {clean_eid} ({notification_type})")
            else:
                print(f"Supabase notification_logs upsert notice: {err}")

        return payload

