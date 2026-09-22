import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app.tests.test_master_verification_suite import TestMasterVerificationSuite, TEST_USER_ID

print("=============================================================")
print("AUTOPAY GUARD MASTER VERIFICATION SUITE (TEST A THROUGH TEST K)")
print(f"Dedicated Test User ID: {TEST_USER_ID}")
print("=============================================================\n")

# Run test setup
TestMasterVerificationSuite.setup_class()

test_cases = [
    ("Test A: New user registration & mock generation", TestMasterVerificationSuite().test_A_new_user_registration_mock_generation),
    ("Test B: Refresh 3x -> no duplicate mock records", TestMasterVerificationSuite().test_B_refresh_3x_no_duplicate_mock_records),
    ("Test C: Logout + login again -> no new mock data", TestMasterVerificationSuite().test_C_logout_and_login_no_new_mock_data),
    ("Test D: Delete subscription -> persists after refresh", TestMasterVerificationSuite().test_D_delete_subscription_persists_after_refresh),
    ("Test E: Update amount/date -> persists after refresh", TestMasterVerificationSuite().test_E_update_amount_date_persists_after_refresh),
    ("Test F: Add subscription -> single calendar event created", TestMasterVerificationSuite().test_F_add_subscription_creates_single_calendar_event),
    ("Test G: Edit subscription date -> same calendar event updated", TestMasterVerificationSuite().test_G_edit_subscription_date_updates_same_calendar_event),
    ("Test H: Delete subscription -> DB record & calendar event deleted", TestMasterVerificationSuite().test_H_delete_subscription_deletes_calendar_event),
    ("Test I: Autopay ON -> OFF -> calendar event removed", TestMasterVerificationSuite().test_I_autopay_on_to_off_removes_calendar_event),
    ("Test J: Autopay OFF -> ON -> single calendar event created", TestMasterVerificationSuite().test_J_autopay_off_to_on_creates_single_calendar_event),
    ("Test K: Billing date reached -> next date calculated correctly", TestMasterVerificationSuite().test_K_billing_date_reached_calculates_next_date),
]

passed_count = 0
failed_count = 0

for name, test_func in test_cases:
    try:
        test_func()
        print(f"✅ PASS | {name}")
        passed_count += 1
    except AssertionError as ae:
        print(f"❌ FAIL | {name}")
        print(f"        AssertionError: {ae}")
        failed_count += 1
    except Exception as ex:
        print(f"❌ FAIL | {name}")
        print(f"        Exception: {ex}")
        failed_count += 1

print("\n=============================================================")
print(f"FINAL SUMMARY: {passed_count}/{len(test_cases)} TESTS PASSED")
print("=============================================================")

if passed_count == len(test_cases):
    print("🎉 ALL 11 MASTER TESTS PASSED 100%! System is stable and verified!")
else:
    print(f"⚠️ {failed_count} test(s) failed. See raw error details above.")
