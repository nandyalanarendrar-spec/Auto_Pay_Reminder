import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app.services.firebase_notification_service import FirebaseNotificationService

TEST_UID = "b214d765-ddd1-4dab-b44a-0162fca19579"

print("=============================================================")
print("VERIFYING FIX FOR 'None' MERCHANT NAME IN REMINDERS API")
print("=============================================================")

alerts = FirebaseNotificationService.get_due_reminders_for_user(TEST_UID)
print(f"Total Due Alerts Found: {len(alerts)}\n")

for i, alert in enumerate(alerts, 1):
    print(f"--- Alert #{i} ---")
    print(f"  ID:                {alert.get('id')}")
    print(f"  Name:              {alert.get('name')}")
    print(f"  Type:              {alert.get('type')}")
    print(f"  Title:             {alert.get('title')}")
    print(f"  Body:              {alert.get('body')}")
    print(f"  Amount:            ₹{alert.get('amount'):,.2f}")
    print(f"  Days Remaining:    {alert.get('days_remaining')}")
    print()

has_none = any("None" in str(alert.get("title")) or "None" in str(alert.get("body")) or alert.get("name") is None for alert in alerts)

if not has_none:
    print("✅ NAME FIX VERIFIED SUCCESSFUL: 0 'None' values found across all reminder alerts!")
else:
    print("❌ ERROR: 'None' still present in reminder alerts!")
