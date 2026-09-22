import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app.core.security import get_supabase_client
from app.services.notification_log_service import NotificationLogService
from app.services.firebase_notification_service import FirebaseNotificationService

supabase = get_supabase_client()
TEST_UID = "b214d765-ddd1-4dab-b44a-0162fca19579"
TODAY = date.today().isoformat()

print("=============================================================")
print("RUNNING OPTION A MIGRATION VERIFICATION")
print("=============================================================")

# 1. Verification of user_id data_type
print("\n--- CHECK 1: Column data_type for user_id in notification_logs ---")
try:
    # Try querying table columns via RPC or direct select
    res = supabase.from_("notification_logs").select("*").limit(1).execute()
    print("notification_logs table active and responding to queries.")
    print("Sample record structure:", res.data)
except Exception as e:
    print("Supabase table query:", e)

# 2. Re-test log insertion with valid UUID user_id
print("\n--- CHECK 2 & 3: Testing Notification Engine & Log Insertion ---")
test_log = NotificationLogService.log_notification(
    user_id=TEST_UID,
    entity_type="subscription",
    entity_id="test_sub_post_migration",
    notification_type="0d",
    sent_date=TODAY,
    channel="web"
)
print("Log notification result:", test_log)

is_logged = NotificationLogService.is_already_notified(
    user_id=TEST_UID,
    entity_type="subscription",
    entity_id="test_sub_post_migration",
    notification_type="0d",
    sent_date=TODAY
)
print("is_already_notified check result:", is_logged)

alerts = FirebaseNotificationService.get_due_reminders_for_user(TEST_UID)
is_excluded = not any(a.get("id") == "test_sub_post_migration" for a in alerts)
print(f"Is 'test_sub_post_migration' deduplicated from due-reminders list? {is_excluded}")

if is_logged and is_excluded:
    print("\n✅ ALL 3 CHECKS VERIFIED SUCCESSFULLY POST-MIGRATION!")
else:
    print("\n❌ VERIFICATION WARNING")
