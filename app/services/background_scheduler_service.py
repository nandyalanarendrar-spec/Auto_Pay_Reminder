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



async def _background_loop(interval_seconds: int = 3600):
    """
    Native async loop running inside the FastAPI process.
    Runs once immediately on startup, then runs periodically.
    """
    global _is_running
    _is_running = True
    print("🚀 [Background Scheduler] In-process scheduler started.")
    
    # Run immediate initial sweep on startup
    try:
        run_daily_rollover_sweep()
    except Exception as e:
        print(f"Startup sweep error: {e}")

    while _is_running:
        try:
            # Sleep for the configured interval (default 1 hour)
            await asyncio.sleep(interval_seconds)
            if not _is_running:
                break
            run_daily_rollover_sweep()
        except asyncio.CancelledError:
            print("🛑 [Background Scheduler] Background task cancelled gracefully.")
            break
        except Exception as err:
            print(f"⚠️ [Background Scheduler] Error in loop: {err}")
            await asyncio.sleep(60)


def start_scheduler():
    """
    Starts the scheduler inside the FastAPI process lifespan / startup event.
    Tries APScheduler if available, otherwise falls back smoothly to asyncio background task.
    """
    global _scheduler_task
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
        # Run daily at midnight IST (00:00)
        scheduler.add_job(
            run_daily_rollover_sweep,
            CronTrigger(hour=0, minute=0, timezone="Asia/Kolkata"),
            id="daily_billing_rollover",
            replace_existing=True
        )
        scheduler.start()
        # Also run initial sweep
        run_daily_rollover_sweep()
        print("✅ [Background Scheduler] APScheduler AsyncIOScheduler started (Trigger: Midnight IST daily).")
        return scheduler
    except ImportError:
        # APScheduler not installed, use native asyncio background task loop
        loop = asyncio.get_event_loop()
        if _scheduler_task is None or _scheduler_task.done():
            _scheduler_task = loop.create_task(_background_loop(interval_seconds=3600))
        print("✅ [Background Scheduler] Native In-Process AsyncIO Scheduler active (hourly sweep + startup sweep).")
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
