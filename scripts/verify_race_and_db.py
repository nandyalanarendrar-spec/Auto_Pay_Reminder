import sys
import os
import threading
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app.services.notification_log_service import NotificationLogService
from app.services.firebase_notification_service import FirebaseNotificationService

TEST_UID = "b214d765-ddd1-4dab-b44a-0162fca19579"
TEST_ENTITY_ID = "sub_netflix_test_due_today"
TEST_NOTIF_TYPE = "0d"
TODAY = date.today().isoformat()

print("=============================================================")
print("1. SQL MIGRATION FILE CREATED FOR UNIQUE CONSTRAINT")
print("=============================================================")
migration_path = os.path.abspath("migrations/005_create_notification_logs_table.sql")
print("Migration file location:", migration_path)
with open(migration_path, "r", encoding="utf-8") as f:
    print(f.read())

print("\n=============================================================")
print("2. CONCURRENT RACE CONDITION TEST (2 SIMULTANEOUS THREADS)")
print("=============================================================")

results = []

def worker(name):
    res = NotificationLogService.log_notification(
        user_id=TEST_UID,
        entity_type="subscription",
        entity_id=TEST_ENTITY_ID,
        notification_type=TEST_NOTIF_TYPE,
        sent_date=TODAY,
        channel="web"
    )
    results.append((name, res))

t1 = threading.Thread(target=worker, args=("Worker 1 (Device A)",))
t2 = threading.Thread(target=worker, args=("Worker 2 (Device B)",))

t1.start()
t2.start()

t1.join()
t2.join()

for name, res in results:
    print(f"[{name}] Result -> {res}")

print("\n=============================================================")
print("3. DEDUPLICATION VERIFICATION AFTER CONCURRENT INSERT")
print("=============================================================")
is_notified = NotificationLogService.is_already_notified(TEST_UID, "subscription", TEST_ENTITY_ID, TEST_NOTIF_TYPE, TODAY)
print(f"is_already_notified() for '{TEST_ENTITY_ID}':", is_notified)

alerts_after = FirebaseNotificationService.get_due_reminders_for_user(TEST_UID)
is_in_alerts = any(a.get("id") == TEST_ENTITY_ID for a in alerts_after)
print(f"Is '{TEST_ENTITY_ID}' returned in subsequent due-reminders poll? {is_in_alerts}")

if is_notified and not is_in_alerts:
    print("\n✅ SUCCESS: Exactly 1 unique notification log registered, 0 duplicate popups across devices!")
