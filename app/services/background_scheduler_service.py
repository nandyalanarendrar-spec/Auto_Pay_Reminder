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

        # 4. Top up demo bank data and refresh the review list for users who loaded the demo
        try:
            from app.services.demo_bank_service import DemoBankService
            demo_res = DemoBankService.run_daily_for_all()
            print(f"🏦 [Background Scheduler] Demo bank update: {demo_res}")
        except Exception as demo_err:
            print("Demo bank daily update error:", demo_err)

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
        from app.routes.personal_reminders import _in_memory_reminders, _in_memory_lock
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
            with _in_memory_lock:
                reminders = [r for r in _in_memory_reminders if not r.get("is_completed")]

        for rem in reminders:
            due_str = rem.get("due_datetime")
            if not due_str:
                continue

            try:
                due_dt = datetime.fromisoformat(str(due_str).replace("Z", "+00:00"))
                if due_dt.tzinfo is None:
                    due_dt = due_dt.replace(tzinfo=IST)
                now_compare = datetime.now(IST)
                diff_seconds = (due_dt - now_compare).total_seconds()
                rem_mins = max(0, int(round(diff_seconds / 60.0)))
                user_offsets = rem.get("reminder_offsets") or [10, 30, 60]
                user_id = str(rem.get("user_id", "default_user")).strip('"\'')
                task_title = rem.get("title") or "Personal Task"
                due_time_str = due_dt.strftime("%I:%M %p, %a %d %b")

                # --- 1. APP PUSH NOTIFICATIONS: User selected offsets + Guaranteed exact due time (0m) ---
                # Threshold-based (not a narrow window): fires as soon as the countdown has crossed at
                # or below the offset mark and hasn't been logged yet, so a delayed/restarted sweep still
                # "catches up" on a missed offset instead of skipping it forever. Bounded below at -120s
                # (the auto-complete cutoff) so a very stale reminder doesn't fire retroactively.
                app_push_offsets = sorted(list(set(user_offsets + [0])))
                for offset_mins in app_push_offsets:
                    offset_secs = offset_mins * 60
                    if -120 <= diff_seconds <= (offset_secs + 5):
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
                            NotificationLogService.log_notification(user_id, "personal_reminder", rem_id, notif_type, channel="fcm")
                            print(f"🔔 [APP PUSH FIRED] Task: '{task_title}' ({push_title})")

                # --- 2. WHATSAPP ALERT: Fixed 1 Hour Before ONLY (60m before) if WhatsApp enabled ---
                # Same threshold-based catch-up approach as the app push above.
                sync_wa = rem.get("sync_whatsapp") if rem.get("sync_whatsapp") is not None else True
                if sync_wa:
                    wa_offset_secs = 60 * 60 # Fixed 1 hour before
                    if -120 <= diff_seconds <= (wa_offset_secs + 15):
                        rem_id = str(rem.get("id"))
                        notif_type = "offset_60m_whatsapp"

                        if not NotificationLogService.is_already_notified(user_id, "personal_reminder", rem_id, notif_type, today_iso):
                            target_phone = getattr(settings, "WHATSAPP_TEST_RECIPIENT", "") or "919014220155"
                            time_label = f"{rem_mins} minutes" if rem_mins < 60 else f"{rem_mins // 60} hour(s)"
                            wa_body = (
                                f"⚡ *Autopay Guard Task Alert (1 Hour Reminder)*\n\n"
                                f"Task: *{task_title}*\n"
                                f"Status: Due in *{time_label}* (at {due_time_str})\n"
                                f"Notes: {rem.get('notes') or 'None'}\n\n"
                                f"🛡️ *Autopay Guard Safety Assistant*"
                            )
                            wa_result = WhatsAppService.send_whatsapp_message(to_phone=target_phone, text_body=wa_body)
                            if wa_result.get("status") != "error":
                                NotificationLogService.log_notification(user_id, "personal_reminder", rem_id, notif_type, channel="whatsapp")
                                print(f"💬 [WHATSAPP FIRED 1H BEFORE] Task: '{task_title}' -> Sent WhatsApp Alert!")
                            else:
                                print(f"⚠️ [WHATSAPP SEND FAILED] Task: '{task_title}' -> will retry next sweep: {wa_result.get('error')}")

                # --- 3. AUTO-COMPLETE ELAPSED TASKS & PURGE GOOGLE CALENDAR EVENT ---
                # 20s past due (not the old 2 minutes) — still one sweep tick of buffer after the
                # "due now" (0m) push notification's own window so it isn't cut off, but the status
                # now flips close to the actual due time instead of lagging behind it.
                if diff_seconds < -20 and not rem.get("is_completed"):
                    rem_id = str(rem.get("id"))
                    cal_ev_id = rem.get("calendar_event_id")

                    # Repeating reminders roll to their next occurrence instead of completing.
                    from app.routes.personal_reminders import roll_reminder_forward, normalize_repeat
                    if normalize_repeat(rem.get("repeat")) != "none":
                        rolled = roll_reminder_forward(rem)
                        if rolled:
                            print(f"🔁 [REPEAT ROLLED] '{task_title}' -> next due {rolled.get('due_datetime')}")
                            continue

                    try:
                        if supabase:
                            supabase.from_("personal_reminders").update({
                                "is_completed": True,
                                "completed_at": datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S+05:30")
                            }).eq("id", rem_id).execute()
                        rem["is_completed"] = True
                        rem["completed_at"] = datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S+05:30")
                        with _in_memory_lock:
                            for mem_r in _in_memory_reminders:
                                if mem_r.get("id") == rem_id:
                                    mem_r["is_completed"] = True
                                    mem_r["completed_at"] = rem["completed_at"]
                                    break
                        
                        from app.services.google_calendar_service import GoogleCalendarService
                        GoogleCalendarService.delete_event_by_id_or_metadata(
                            user_id=user_id,
                            event_id=cal_ev_id,
                            private_props={"personal_reminder_id": rem_id}
                        )
                        print(f"✅ [AUTO-COMPLETED ELAPSED TASK] '{task_title}' (ID: {rem_id}) -> Marked completed & purged from Google Calendar!")
                    except Exception as auto_comp_err:
                        print("Auto-complete elapsed task error:", auto_comp_err)

            except Exception as item_err:
                print("Item check error:", item_err)
    except Exception as e:
        print("Personal reminders sweep error:", e)


def run_completed_tasks_auto_purge():
    """
    Auto-purge sweep: Deletes completed personal reminders that were completed more than 24 hours ago.
    Keeps completed tasks visible in the 'Completed History' section for 1 day before cleanup.
    """
    try:
        from app.core.security import get_supabase_client
        from app.routes.personal_reminders import _in_memory_reminders, _in_memory_lock

        now = datetime.now(IST)
        cutoff = now - timedelta(hours=24)
        cutoff_iso = cutoff.strftime("%Y-%m-%dT%H:%M:%S+05:30")

        purged_count = 0

        # 1. Purge from Supabase DB
        try:
            supabase = get_supabase_client()
            if supabase:
                # Fetch completed tasks with completed_at older than 24 hours
                res = supabase.from_("personal_reminders").select("id, title, completed_at").eq("is_completed", True).lt("completed_at", cutoff_iso).execute()
                if res.data:
                    for row in res.data:
                        task_id = row.get("id")
                        task_title = row.get("title", "Unknown")
                        try:
                            supabase.from_("personal_reminders").delete().eq("id", task_id).execute()
                            purged_count += 1
                            print(f"🗑️ [AUTO-PURGE] Deleted completed task '{task_title}' (ID: {task_id}) — completed 24+ hours ago.")
                        except Exception as del_err:
                            print(f"Auto-purge delete error for {task_id}: {del_err}")
        except Exception as db_err:
            print("Auto-purge Supabase error:", db_err)

        # 2. Purge from in-memory fallback
        with _in_memory_lock:
            ids_to_remove = []
            for r in _in_memory_reminders:
                if r.get("is_completed") and r.get("completed_at"):
                    try:
                        comp_dt = datetime.fromisoformat(str(r["completed_at"]).replace("Z", "+00:00"))
                        if comp_dt.tzinfo is None:
                            comp_dt = comp_dt.replace(tzinfo=IST)
                        if comp_dt < cutoff:
                            ids_to_remove.append(r.get("id"))
                            purged_count += 1
                    except Exception:
                        pass

            if ids_to_remove:
                _in_memory_reminders[:] = [r for r in _in_memory_reminders if r.get("id") not in ids_to_remove]

        if purged_count > 0:
            print(f"✅ [AUTO-PURGE] Cleaned up {purged_count} completed task(s) older than 24 hours.")

    except Exception as e:
        print(f"Auto-purge sweep error: {e}")


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
                run_completed_tasks_auto_purge()

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

