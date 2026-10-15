"""Alerts for the two things users most want to hear about right away: a price hike and a trial that became paid."""
from typing import Any, Dict, Iterable, List

from app.services.transaction_store import clean_user_id

# One alert per (item, kind) for good: notification_logs dedupes on a date, so every send uses the same one.
ALERT_SENT_DATE = "2000-01-01"
KINDS = ("price_hike", "trial_converted")


def _rupees(value: Any) -> str:
    try:
        return f"₹{float(value):,.0f}"
    except (ValueError, TypeError):
        return "₹0"


def build_alerts(items: Iterable[dict]) -> List[Dict[str, Any]]:
    """Pure function: turn pending detected items into user-facing alerts."""
    alerts: List[Dict[str, Any]] = []
    for item in items:
        if item.get("status", "pending") != "pending":
            continue
        flags = item.get("flags") or []
        details = item.get("details") or {}
        name = item.get("merchant_name") or "A payment"
        base = {"item_id": item.get("id"), "merchant_name": name, "kind_of_item": item.get("kind")}

        if "price_hike" in flags:
            old, new = details.get("old_amount"), details.get("new_amount") or item.get("amount")
            try:
                extra = float(new) - float(old)
            except (ValueError, TypeError):
                extra = 0.0
            message = f"{name} now costs {_rupees(new)} (was {_rupees(old)})."
            if extra > 0:
                message += f" That is {_rupees(extra * 12)} more per year."
            alerts.append({**base, "kind": "price_hike", "title": f"{name} price went up", "message": message,
                           "old_amount": old, "new_amount": new})

        if "trial_converted" in flags:
            trial, now_amount = details.get("trial_amount"), item.get("amount")
            message = (f"The {_rupees(trial)} trial has turned into a paid plan of {_rupees(now_amount)} per month. "
                       f"Cancel it if you no longer use it.")
            alerts.append({**base, "kind": "trial_converted", "title": f"{name} trial is now paid",
                           "message": message, "trial_amount": trial, "new_amount": now_amount})
    return alerts


class InsightAlertService:
    @staticmethod
    def get_alerts(user_id: Any) -> List[Dict[str, Any]]:
        from app.core.security import get_supabase_client

        uid = clean_user_id(user_id)
        if not uid:
            return []
        try:
            rows = (
                get_supabase_client().from_("detected_items")
                .select("id,kind,merchant_name,amount,flags,details,status")
                .eq("user_id", uid).eq("status", "pending").execute().data or []
            )
        except Exception as err:
            print("Insight alerts read note:", err)
            return []
        return build_alerts(rows)

    @staticmethod
    def notify_new(user_id: Any) -> int:
        """Send one push per new alert (never twice). Returns how many were sent. Never raises."""
        try:
            from app.services.firebase_notification_service import FirebaseNotificationService
            from app.services.notification_log_service import NotificationLogService

            uid = clean_user_id(user_id)
            if not uid:
                return 0
            sent = 0
            for alert in InsightAlertService.get_alerts(uid):
                item_id = str(alert["item_id"])
                if NotificationLogService.is_already_notified(uid, "detected_item", item_id, alert["kind"], ALERT_SENT_DATE):
                    continue
                FirebaseNotificationService.send_push_notification(
                    user_id=uid, title=alert["title"], body=alert["message"],
                    data={"type": alert["kind"], "id": item_id},
                )
                NotificationLogService.log_notification(
                    uid, "detected_item", item_id, alert["kind"], sent_date=ALERT_SENT_DATE, channel="fcm"
                )
                sent += 1
            return sent
        except Exception as err:
            print("Insight alert notify note:", err)
            return 0
