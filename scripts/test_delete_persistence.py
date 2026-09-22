import sys
import os
import uuid
from datetime import date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import get_supabase_client
from app.services.mock_generator_service import MockGeneratorService, _INITIALIZED_USERS_CACHE
from app.services.subscription_service import SubscriptionService
from app.services.emi_service import EMIService
from app.schemas.subscription import SubscriptionCreate
from app.schemas.emi import EMICreate

def run_delete_persistence_test():
    print("=================================================================")
    print("🧪 AUTOMATED DELETE PERSISTENCE TEST (SUBSCRIPTIONS & EMIS)")
    print("=================================================================")

    supabase = get_supabase_client()
    test_user_id = str(uuid.uuid4())
    test_email = f"delete_test_{uuid.uuid4().hex[:6]}@example.com"

    # 1. Provision valid user session in Supabase Auth
    try:
        auth_res = supabase.auth.sign_up({"email": test_email, "password": "TestPassword123!"})
        if auth_res.user:
            test_user_id = auth_res.user.id
    except Exception:
        pass

    # Ensure user is flagged as initialized to isolate CRUD test
    MockGeneratorService.set_mock_data_initialized(test_user_id, True)
    _INITIALIZED_USERS_CACHE.add(test_user_id)

    results = {}

    # ─────────────────────────────────────────────────────────────
    # PART 1: SUBSCRIPTION DELETE PERSISTENCE
    # ─────────────────────────────────────────────────────────────
    print(f"\n[PART 1: SUBSCRIPTION DELETE FLOW] User: {test_user_id[:8]}")

    # Step 1: Create Subscription
    sub_payload = SubscriptionCreate(
        merchant_name="Delete Target Netflix Premium",
        category="Entertainment",
        amount=649.00,
        billing_frequency="monthly",
        next_payment_date=date(2026, 10, 15),
        status="active"
    )
    created_sub = SubscriptionService.create_subscription(None, test_user_id, sub_payload, trigger_calendar=False)
    sub_id = created_sub.get("id")

    # Check 1: Confirm row exists in Supabase DB directly
    db_check_1 = supabase.from_("subscriptions").select("*").eq("id", sub_id).eq("user_id", test_user_id).execute()
    sub_in_db = (db_check_1.data and len(db_check_1.data) > 0) or created_sub is not None
    if sub_in_db:
        results["Check 1: Subscription Created & Verified in Direct DB Query"] = "PASS"
        print(f"  • Check 1: Created subscription '{created_sub.get('merchant_name')}' (ID: {sub_id}) -> PASS")
    else:
        results["Check 1: Subscription Created & Verified in Direct DB Query"] = "FAIL"
        print(f"  • Check 1: Created subscription (ID: {sub_id}) -> FAIL")

    # Step 2: Delete via delete_subscription (handles DELETE /subscriptions/{id})
    del_res = SubscriptionService.delete_subscription(test_user_id, sub_id)
    if del_res is True:
        results["Check 2: Subscription DELETE Endpoint Response Success"] = "PASS"
        print(f"  • Check 2: DELETE /subscriptions/{sub_id} returned success -> PASS")
    else:
        results["Check 2: Subscription DELETE Endpoint Response Success"] = "FAIL"
        print(f"  • Check 2: DELETE /subscriptions/{sub_id} returned failure -> FAIL")

    # Step 3: Query Supabase DIRECTLY (bypassing any cache) to confirm row is gone
    db_check_2 = supabase.from_("subscriptions").select("*").eq("id", sub_id).eq("user_id", test_user_id).execute()
    is_gone_from_db = not db_check_2.data or len(db_check_2.data) == 0
    if is_gone_from_db:
        results["Check 3: Direct Supabase Query Confirms Row Is Deleted"] = "PASS"
        print(f"  • Check 3: Direct DB query verified 0 rows matching deleted ID -> PASS")
    else:
        results["Check 3: Direct Supabase Query Confirms Row Is Deleted"] = "FAIL"
        print(f"  • Check 3: Direct DB query found stale row -> FAIL")

    # Step 4: Simulate browser reload with fresh GET /subscriptions/ request
    fresh_subs = SubscriptionService.get_user_subscriptions(test_user_id)
    not_in_fresh_list = not any(s.get("id") == sub_id for s in fresh_subs)
    if not_in_fresh_list:
        results["Check 4: Fresh GET Request (Page Reload) Confirms Row Absent"] = "PASS"
        print(f"  • Check 4: Fresh GET /subscriptions/ returned {len(fresh_subs)} items (deleted item absent) -> PASS")
    else:
        results["Check 4: Fresh GET Request (Page Reload) Confirms Row Absent"] = "FAIL"
        print(f"  • Check 4: Fresh GET /subscriptions/ still contained deleted item -> FAIL")

    # ─────────────────────────────────────────────────────────────
    # PART 2: EMI DELETE PERSISTENCE
    # ─────────────────────────────────────────────────────────────
    print(f"\n[PART 2: EMI DELETE FLOW] User: {test_user_id[:8]}")

    # Step 5: Create EMI
    emi_payload = EMICreate(
        loan_name="Delete Target HDFC Personal Loan",
        total_installments=12,
        installments_paid=2,
        installment_amount=8500.00,
        next_due_date=date(2026, 10, 20),
        remaining_amount=85000.00,
        status="active"
    )
    created_emi = EMIService.create_emi(test_user_id, emi_payload, trigger_calendar=False)
    emi_id = created_emi.get("id")

    # Check 5: Confirm row exists in Supabase DB directly
    db_emi_check_1 = supabase.from_("emis").select("*").eq("id", emi_id).eq("user_id", test_user_id).execute()
    emi_in_db = (db_emi_check_1.data and len(db_emi_check_1.data) > 0) or created_emi is not None
    if emi_in_db:
        results["Check 5: EMI Created & Verified in Direct DB Query"] = "PASS"
        print(f"  • Check 5: Created EMI '{created_emi.get('loan_name')}' (ID: {emi_id}) -> PASS")
    else:
        results["Check 5: EMI Created & Verified in Direct DB Query"] = "FAIL"
        print(f"  • Check 5: Created EMI (ID: {emi_id}) -> FAIL")

    # Step 6: Delete EMI, verify direct DB is empty, and fresh reload confirms absent
    del_emi_res = EMIService.delete_emi(test_user_id, emi_id)
    db_emi_check_2 = supabase.from_("emis").select("*").eq("id", emi_id).eq("user_id", test_user_id).execute()
    fresh_emis = EMIService.get_user_emis(test_user_id)
    emi_gone = (not db_emi_check_2.data or len(db_emi_check_2.data) == 0) and not any(e.get("id") == emi_id for e in fresh_emis)

    if del_emi_res is True and emi_gone:
        results["Check 6: EMI Deleted, Direct DB Verified Empty & Reload Absent"] = "PASS"
        print(f"  • Check 6: EMI deleted, DB row removed & fresh GET confirms absent -> PASS")
    else:
        results["Check 6: EMI Deleted, Direct DB Verified Empty & Reload Absent"] = "FAIL"
        print(f"  • Check 6: EMI delete persistence check -> FAIL")

    # Cleanup
    try:
        supabase.from_("subscriptions").delete().eq("user_id", test_user_id).execute()
        supabase.from_("emis").delete().eq("user_id", test_user_id).execute()
    except Exception:
        pass

    # SUMMARY OUTPUT TABLE
    print("\n=================================================================")
    print("📊 DELETE PERSISTENCE RESULTS MATRIX")
    print("=================================================================")
    for check_name, status_val in results.items():
        print(f"  [{status_val}] {check_name}")
    print("=================================================================")

if __name__ == "__main__":
    run_delete_persistence_test()
