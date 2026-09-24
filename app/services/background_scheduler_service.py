"""
Background Scheduled Job Service for Autopay Guard.
Periodically (and at startup / midnight IST) sweeps all active subscriptions and EMIs in Supabase DB:
1. Rollover overdue active subscriptions (next_payment_date < today)
2. Rollover expired free trials (trial_end_date <= today) to active subscriptions
3. Rollover overdue active EMIs (next_due_date < today)
4. Auto-sync updated dates to Google Calendar in-place via PATCH
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("autopay.scheduler")

_scheduler_task: Optional[asyncio.Task] = None
_is_running = False

# IST Timezone (+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def run_daily_rollover_sweep():
    """
    Executes a complete sweep of all overdue subscriptions and EMIs + dispatches payment due reminders.
    Callable by APScheduler or asyncio background loop.
    """
    try:
        from app.services.subscription_service import SubscriptionService
        from app.services.emi_service import EMIService
        from app.services.firebase_notification_service import FirebaseNotificationService

        now_ist = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        print(f"⏰ [Background Scheduler] Running daily rollover & reminder sweep at {now_ist}...")

        # 1. Rollover overdue subscriptions & trials across all users
        rolled_subs = SubscriptionService.auto_rollover_overdue_subscriptions()
        print(f"✅ [Background Scheduler] Rolled forward {len(rolled_subs)} subscriptions/trials.")

        # 2. Rollover overdue EMIs across all users
        rolled_emis = EMIService.auto_rollover_overdue_emis()
        print(f"✅ [Background Scheduler] Rolled forward {len(rolled_emis)} EMI loan records.")

        # 3. Check & dispatch payment due push notifications (7, 3, 1, 0 days window)
        reminder_res = FirebaseNotificationService.run_daily_payment_reminder_job()
        print(f"🔔 [Background Scheduler] Scanned upcoming payment reminders: {reminder_res.get('reminders_count', 0)} alerts sent.")

        return {
            "status": "success",
            "subscriptions_updated": len(rolled_subs),
            "emis_updated": len(rolled_emis),
            "reminders_dispatched": reminder_res.get("reminders_count", 0),
            "timestamp": now_ist
        }
    except Exception as e:
        print(f"❌ [Background Scheduler] Error during rollover & reminder sweep: {e}")
        return {"status": "error", "message": str(e)}



def run_high_frequency_personal_reminders_sweep():
    """
    High-frequency real-time ticker running every 15 seconds.
    Scans all active personal custom reminders against current time and configured alert offsets (10m, 30m, 1h, 1d).
    Dispatches FCM Web/Mobile Push Notifications and WhatsApp alerts when an offset window is entered.
    """
    try:
        from app.core.config import settings
        from app.core.security import get_supabase_client
        from app.services.notification_log_service import NotificationLogService
        from app.services.firebase_notification_service import FirebaseNotificationService
        from app.services.whatsapp_service import WhatsAppService
        from app.routes.personal_reminders import _in_memory_reminders
        from datetime import datetime, date, timezone

        today_iso = date.today().isoformat()
        now = datetime.now()

        # Query active personal reminders from Supabase or memory fallback
        reminders = []
        try:
            supabase = get_supabase_client()
            if supabase:
                res = supabase.from_("personal_reminders").select("*").eq("is_completed", False).execute()
                if res.data:
                    reminders = res.data
        except Exception:
            pass

        if not reminders:
            reminders = [r for r in _in_memory_reminders if not r.get("is_completed")]

        for rem in reminders:
            due_str = rem.get("due_datetime")
            if not due_str:
                continue

            try:
                clean_due = str(due_str).replace("Z", "").split("+")[0]
                due_dt = datetime.fromisoformat(clean_due)
                now_compare = datetime.now()
                diff_seconds = (due_dt - now_compare).total_seconds()
                rem_mins = max(0, int(round(diff_seconds / 60.0)))
                user_offsets = rem.get("reminder_offsets") or [10, 30, 60]
                user_id = str(rem.get("user_id", "default_user")).strip('"\'')
                task_title = rem.get("title") or "Personal Task"
                due_time_str = due_dt.strftime("%I:%M %p, %a %d %b")

                # --- 1. APP PUSH NOTIFICATIONS: User selected offsets + Guaranteed exact due time (0m) ---
                app_push_offsets = sorted(list(set(user_offsets + [0])))
                for offset_mins in app_push_offsets:
                    offset_secs = offset_mins * 60
                    # Firing window: trigger when diff_seconds is between offset_secs - 30 and offset_secs + 5
                    if (offset_secs - 30) <= diff_seconds <= (offset_secs + 5):
                        rem_id = str(rem.get("id"))
                        notif_type = f"offset_{offset_mins}m_push"

                        if not NotificationLogService.is_already_notified(user_id, "personal_reminder", rem_id, notif_type, today_iso):
                            if offset_mins == 0 or rem_mins == 0:
                                push_title = f"🚨 Task Due NOW: {task_title}"
                                push_body = f"Your personal reminder '{task_title}' is DUE NOW! ({due_time_str})"
                            else:
                                offset_label = f"{rem_mins} minutes" if rem_mins < 60 else f"{rem_mins // 60} hour(s)"
                                push_title = f"⏰ Task Reminder: {task_title}"
                                push_body = f"Your task '{task_title}' is due in {offset_label}! ({due_time_str})"

                            FirebaseNotificationService.send_push_notification(
                                user_id=user_id,
                                title=push_title,
                                body=push_body,
                                data={"type": "personal_reminder", "id": rem_id}
                            )
                            NotificationLogService.log_notification(user_id, "personal_reminder", rem_id, notif_type, "fcm")
                            print(f"🔔 [APP PUSH FIRED] Task: '{task_title}' ({push_title})")

                # --- 2. WHATSAPP ALERT: Fixed 1 Hour Before ONLY (60m before) if WhatsApp enabled ---
                sync_wa = rem.get("sync_whatsapp") if rem.get("sync_whatsapp") is not None else True
                if sync_wa:
                    wa_offset_secs = 60 * 60 # Fixed 1 hour before
                    if (wa_offset_secs - 45) <= diff_seconds <= (wa_offset_secs + 15):
                        rem_id = str(rem.get("id"))
                        notif_type = "offset_60m_whatsapp"

                        if not NotificationLogService.is_already_notified(user_id, "personal_reminder", rem_id, notif_type, today_iso):
                            target_phone = getattr(settings, "WHATSAPP_TEST_RECIPIENT", "") or "919014220155"
                            wa_body = (
                                f"⚡ *Autopay Guard Task Alert (1 Hour Reminder)*\n\n"
                                f"Task: *{task_title}*\n"
                                f"Status: Due in *1 Hour* (at {due_time_str})\n"
                                f"Notes: {rem.get('notes') or 'None'}\n\n"
                                f"🛡️ *Autopay Guard Safety Assistant*"
                            )
                            WhatsAppService.send_whatsapp_message(to_phone=target_phone, text_body=wa_body)
                            NotificationLogService.log_notification(user_id, "personal_reminder", rem_id, notif_type, "whatsapp")
                            print(f"💬 [WHATSAPP FIRED 1H BEFORE] Task: '{task_title}' -> Sent WhatsApp Alert!")

            except Exception as item_err:
                print("Item check error:", item_err)
    except Exception as e:
        print("Personal reminders sweep error:", e)


async def _background_loop(interval_seconds: int = 15):
    """
    Native async loop running inside the FastAPI process.
    Runs high-frequency personal reminder checks every 15 seconds, and daily rollover every hour.
    """
    global _is_running
    _is_running = True
    print("🚀 [Background Scheduler] In-process real-time scheduler started (15s ticker active).")
    
    # Run immediate initial sweep on startup
    try:
        run_daily_rollover_sweep()
    except Exception as e:
        print(f"Startup sweep error: {e}")

    counter = 0
    while _is_running:
        try:
            # High frequency check every 15 seconds
            await asyncio.sleep(15)
            if not _is_running:
                break
            
            run_high_frequency_personal_reminders_sweep()

            counter += 15
            if counter >= 3600: # Every 1 hour
                counter = 0
                run_daily_rollover_sweep()

        except asyncio.CancelledError:
            print("🛑 [Background Scheduler] Background task cancelled gracefully.")
            break
        except Exception as err:
            print(f"⚠️ [Background Scheduler] Error in loop: {err}")
            await asyncio.sleep(15)


def start_scheduler():
    """
    Starts the scheduler inside the FastAPI process lifespan / startup event.
    """
    global _scheduler_task
    loop = asyncio.get_event_loop()
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = loop.create_task(_background_loop(interval_seconds=15))
    print("✅ [Background Scheduler] Real-time In-Process AsyncIO Scheduler active (15-second offset ticker + daily sweep).")
    return _scheduler_task


def stop_scheduler():
    """
    Stops background tasks gracefully on server shutdown.
    """
    global _is_running, _scheduler_task
    _is_running = False
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
    print("🛑 [Background Scheduler] Stopped.")

