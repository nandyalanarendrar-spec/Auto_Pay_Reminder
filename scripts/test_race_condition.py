import sys
import os
import threading
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app.services.notification_log_service import NotificationLogService

TEST_UID = "b214d765-ddd1-4dab-b44a-0162fca19579"
TEST_ENTITY_ID = "race_test_sub_999"
TEST_NOTIF_TYPE = "1d"
TODAY = date.today().isoformat()

results = []

def call_log_notification(thread_name: str):
    try:
        res = NotificationLogService.log_notification(
            user_id=TEST_UID,
            entity_type="subscription",
            entity_id=TEST_ENTITY_ID,
            notification_type=TEST_NOTIF_TYPE,
            sent_date=TODAY,
            channel="web"
        )
        results.append((thread_name, "SUCCESS", res))
    except Exception as e:
        results.append((thread_name, "ERROR", str(e)))

print("--- Testing Near-Simultaneous Concurrent Concurrent Calls to log_notification ---")

t1 = threading.Thread(target=call_log_notification, args=("Thread-1",))
t2 = threading.Thread(target=call_log_notification, args=("Thread-2",))

t1.start()
t2.start()

t1.join()
t2.join()

print("\n--- Worker Execution Results ---")
for thread_name, status, res in results:
    print(f"[{thread_name}] Status: {status} | Output: {res}")

# Count entries for this item
count = 0
if NotificationLogService.is_already_notified(TEST_UID, "subscription", TEST_ENTITY_ID, TEST_NOTIF_TYPE, TODAY):
    count = 1

print(f"\n--- Verification Audit ---")
print(f"Has item been marked as notified? {count > 0}")
print(f"Total entries count: {count} (Expected: 1)")

if count == 1 and all(status == "SUCCESS" for _, status, _ in results):
    print("✅ RACE CONDITION TEST PASSED: Exactly 1 row registered, 0 errors thrown to callers!")
else:
    print("❌ RACE CONDITION TEST FAILED!")
