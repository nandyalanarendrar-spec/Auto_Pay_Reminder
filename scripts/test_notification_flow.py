import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app.services.firebase_notification_service import FirebaseNotificationService
from app.services.background_scheduler_service import run_daily_rollover_sweep

print('--- Testing get_due_reminders_for_user ---')
alerts = FirebaseNotificationService.get_due_reminders_for_user('default_user')
print(f'Found {len(alerts)} due alerts for default_user:')
for a in alerts:
    print('  -', a)

print('\n--- Testing run_daily_payment_reminder_job ---')
job_res = FirebaseNotificationService.run_daily_payment_reminder_job('default_user')
print('Job result:', job_res)

print('\n--- Testing run_daily_rollover_sweep ---')
sweep_res = run_daily_rollover_sweep()
print('Sweep result:', sweep_res)
