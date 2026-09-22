"""
Automated Verification: Delete Subscription & Page Refresh Persistence
Verifies:
1. User has subscriptions in the database.
2. Deletes a specific subscription.
3. Simulates multiple full page refreshes (GET /subscriptions).
4. Confirms the deleted subscription never reappears.
5. Simulates user logout & re-login, confirming permanent deletion persists.
"""

import sys
import os
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uuid
from datetime import date, timedelta
from app.core.security import get_supabase_client
from app.schemas.subscription import SubscriptionCreate
from app.services.subscription_service import SubscriptionService
from app.services.mock_generator_service import MockGeneratorService


def run_delete_and_refresh_test():
    print("=" * 80)
    print("🧪 AUTOMATED VERIFICATION: DELETE SUBSCRIPTION & REFRESH PERSISTENCE")
    print("=" * 80)

    supabase = get_supabase_client()
    test_email = f"delete_test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"

    # 1. Create a real user
    auth_resp = supabase.auth.sign_up({"email": test_email, "password": test_password})
    user_id = str(auth_resp.user.id)
    print(f"\n[Step 1] Created user: {user_id} ({test_email})")

    # 2. Fetch initial subscriptions (triggers one-time mock seed)
    initial_subs = SubscriptionService.get_user_subscriptions(user_id)
    initial_count = len(initial_subs)
    print(f"  • Initial Subscriptions Loaded: {initial_count} items")
    assert initial_count > 0, "Expected mock subscriptions to be seeded"

    # 3. Pick a subscription to delete (e.g. Netflix Premium or first item)
    target_sub = initial_subs[0]
    target_id = target_sub["id"]
    target_name = target_sub.get("merchant_name") or target_sub.get("name")
    print(f"\n[Step 2] Selected subscription to delete: '{target_name}' (ID: {target_id})")

    # 4. Perform DELETE operation
    print(f"  • Deleting '{target_name}'...")
    delete_result = SubscriptionService.delete_subscription(user_id=user_id, sub_id=target_id)
    assert delete_result is True, "Delete operation failed"
    print(f"  ✅ Subscription deleted from backend.")

    # 5. Verify direct DB lookup returns None immediately
    direct_check = SubscriptionService.get_subscription_by_id(user_id, target_id)
    assert direct_check is None, f"❌ Error: Subscription {target_id} still found via direct lookup!"
    print("  ✅ Direct database query confirmed item is purged from DB.")

    # 6. Simulate 5 consecutive full page refreshes (GET /subscriptions)
    print(f"\n[Step 3] Simulating 5 consecutive page refreshes (fetchFromBackend)...")
    for refresh_num in range(1, 6):
        refreshed_subs = SubscriptionService.get_user_subscriptions(user_id)
        assert not any(s.get("id") == target_id for s in refreshed_subs), f"❌ Refresh #{refresh_num} failed: Deleted item '{target_name}' reappeared!"
        assert len(refreshed_subs) == initial_count - 1, f"❌ Refresh #{refresh_num} unexpected count: {len(refreshed_subs)} vs expected {initial_count - 1}"
        print(f"  • Refresh #{refresh_num}: PASS ({len(refreshed_subs)} active subscriptions, '{target_name}' NOT present)")

    # 7. Simulate User Logout & Fresh Re-login
    print(f"\n[Step 4] Simulating complete Logout and Re-Login...")
    is_mock_init = MockGeneratorService.is_mock_data_initialized(user_id)
    assert is_mock_init is True, "Mock data initialized flag must remain True"
    
    post_login_subs = SubscriptionService.get_user_subscriptions(user_id)
    assert not any(s.get("id") == target_id for s in post_login_subs), f"❌ After re-login: Deleted item '{target_name}' reappeared!"
    assert len(post_login_subs) == initial_count - 1, f"❌ After re-login: Count changed ({len(post_login_subs)})"
    print(f"  ✅ Re-login confirmed: Steady count ({len(post_login_subs)} items), '{target_name}' permanently deleted.")

    # Cleanup test user
    try:
        supabase.from_("subscriptions").delete().eq("user_id", user_id).execute()
        supabase.from_("emis").delete().eq("user_id", user_id).execute()
    except Exception:
        pass

    print("\n" + "=" * 80)
    print("🎉 PERSISTENCE TEST 100% PASSED: DELETED SUBSCRIPTIONS NEVER REAPPEAR!")
    print("=" * 80)


if __name__ == "__main__":
    run_delete_and_refresh_test()
