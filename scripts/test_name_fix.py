import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app.services.firebase_notification_service import FirebaseNotificationService
from app.services.subscription_service import SubscriptionService

TEST_UID = "b214d765-ddd1-4dab-b44a-0162fca19579"

subs = SubscriptionService.get_user_subscriptions(TEST_UID)
print("--- Raw Subscriptions Database Records ---")
for s in subs[:5]:
    print("Sub:", {
        "id": s.get("id"),
        "merchant_name": s.get("merchant_name"),
        "name": s.get("name"),
        "amount": s.get("amount")
    })
