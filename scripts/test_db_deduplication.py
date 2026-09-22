import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app.services.notification_log_service import NotificationLogService
from app.services.firebase_notification_service import FirebaseNotificationService

TEST_UID = "b214d765-ddd1-4dab-b44a-0162fca19579"

print("--- 1. Testing Initial Backend Due Reminders Fetch ---")
alerts_1 = FirebaseNotificationService.get_due_reminders_for_user(TEST_UID)
print(f"Fetch 1 returned {len(alerts_1)} pending due alerts.")
for a in alerts_1:
    print("  Alert:", a.get("name"), "| Type:", a.get("type"), "| NotifType:", a.get("notification_type"), "| Days:", a.get("days_remaining"))

if alerts_1:
    first_item = alerts_1[0]
    print(f"\n--- 2. Simulating Device A displaying alert for '{first_item['name']}' & logging to Backend DB ---")
    log_res = NotificationLogService.log_notification(
        user_id=TEST_UID,
        entity_type=first_item["type"],
        entity_id=first_item["id"],
        notification_type=first_item["notification_type"],
        channel="web"
    )
    print("Logged to DB:", log_res)

    print(f"\n--- 3. Simulating Device B / Incognito Session fetching Backend Due Reminders ---")
    alerts_2 = FirebaseNotificationService.get_due_reminders_for_user(TEST_UID)
    print(f"Fetch 2 returned {len(alerts_2)} pending due alerts.")
    for a in alerts_2:
        print("  Alert:", a.get("name"), "| Type:", a.get("type"), "| NotifType:", a.get("notification_type"))

    item_in_fetch_2 = any(a["id"] == first_item["id"] and a["notification_type"] == first_item["notification_type"] for a in alerts_2)
    if not item_in_fetch_2:
        print("\n✅ DEDUPLICATION VERIFIED SUCCESS: Item was NOT returned to Device B because it was already logged as sent in Backend DB!")
    else:
        print("\n❌ DEDUPLICATION FAILED: Item was re-sent.")
else:
    print("No due alerts found in database for test user.")
