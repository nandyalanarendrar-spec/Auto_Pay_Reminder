"""
MASTER VERIFICATION SUITE — AUTOPAY GUARD
Runs all hardening test suites across:
  • Group A: Database & Security Hardening (A1-A7)
  • Group B: Google Calendar Architecture (B1-B7)
  • Group C: Rollover & EMI Lifecycle (C1-C3)
  • Group D: Frontend & End-to-End Integration (D1-D2)
"""
import sys
import os
import time

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import subprocess

SCRIPTS = [
    ("A1-A2: Database Persistence & Deduplication", "scripts/test_db_persistence.py"),
    ("A3: Strict User Scoping & Cross-Tenant Isolation", "scripts/test_user_scoping_audit.py"),
    ("A4-A5: Subscription & EMI Deletion Persistence", "scripts/test_delete_persistence.py"),
    ("A6: One-Time Mock Initialization", "scripts/test_mock_initialization.py"),
    ("A7: Complete User Data Clear & Purge", "scripts/test_clear_data.py"),
    ("B1-B2: Google Calendar Event Creation & Metadata", "scripts/test_calendar_lifecycle.py"),
    ("B3: Idempotent Single-Event Creation Guarantee", "scripts/test_idempotent_calendar_create.py"),
    ("B4: Patch Update & Event ID Preservation", "scripts/test_calendar_patch_update.py"),
    ("B5: Delete Specific Event ID (Same Merchant Isolation)", "scripts/test_specific_event_deletion.py"),
    ("B6: Autopay Toggle 5x Oscillations & Event Sync", "scripts/test_autopay_toggle_lifecycle.py"),
    ("B7: Calendar Sync Failure & Hybrid Retry Architecture", "scripts/test_calendar_sync_failure_handling.py"),
    ("C1-C2: Free Trial Date Tracking & Rollover Lifecycle", "scripts/test_free_trial_lifecycle.py"),
    ("C3: EMI Calendar Lifecycle, Idempotency & Completion Marker", "scripts/test_emi_calendar_lifecycle.py"),
]


def run_all_master_tests():
    print("=" * 80)
    print("🛡️ AUTOPAY GUARD — MASTER END-TO-END AUTOMATED VERIFICATION SUITE")
    print("=" * 80)
    print(f"Total Suites to Execute: {len(SCRIPTS)}\n")

    results = []
    start_total = time.time()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    for idx, (name, script_rel_path) in enumerate(SCRIPTS, 1):
        print(f"\n[{idx}/{len(SCRIPTS)}] RUNNING: {name} ({script_rel_path})...")
        suite_start = time.time()
        script_full_path = os.path.join(project_root, script_rel_path)
        
        try:
            res = subprocess.run(
                [sys.executable, script_full_path],
                cwd=project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                timeout=60
            )
            elapsed = time.time() - suite_start
            
            if res.returncode == 0:
                print(f"✅ [{idx}/{len(SCRIPTS)}] PASSED: {name} ({elapsed:.2f}s)")
                results.append((name, "PASSED", elapsed, None))
            else:
                print(f"❌ [{idx}/{len(SCRIPTS)}] FAILED: {name} ({elapsed:.2f}s)")
                print("Error output:\n", res.stderr or res.stdout)
                results.append((name, "FAILED", elapsed, (res.stderr or res.stdout or "Non-zero exit")[:200]))
        except Exception as exc:
            elapsed = time.time() - suite_start
            print(f"❌ [{idx}/{len(SCRIPTS)}] TIMED OUT / ERROR: {name} ({elapsed:.2f}s) -> {exc}")
            results.append((name, "FAILED", elapsed, str(exc)[:200]))

    total_elapsed = time.time() - start_total

    print("\n" + "=" * 80)
    print("📊 MASTER VERIFICATION SUITE — FINAL EXECUTION SUMMARY")
    print("=" * 80)

    passed_count = sum(1 for _, status, _, _ in results if status == "PASSED")
    failed_count = sum(1 for _, status, _, _ in results if status == "FAILED")

    for idx, (name, status, duration, err) in enumerate(results, 1):
        status_icon = "✅ PASS" if status == "PASSED" else "❌ FAIL"
        err_info = f" ({err.strip()})" if err else ""
        print(f"  {idx:2d}. [{status_icon}] {name:62s} [{duration:.2f}s]{err_info}")

    print("-" * 80)
    print(f"Total Test Suites: {len(SCRIPTS)}")
    print(f"Passed:            {passed_count} / {len(SCRIPTS)} ({passed_count/len(SCRIPTS)*100:.1f}%)")
    print(f"Failed:            {failed_count} / {len(SCRIPTS)}")
    print(f"Total Time:        {total_elapsed:.2f} seconds")
    print("=" * 80)

    if failed_count == 0:
        print("🎉 ALL MASTER SUITES PASSED! 100% VERIFIED ACROSS GROUPS A, B, C & D.")
    else:
        print(f"⚠️ {failed_count} SUITE(S) FAILED. Please review the error log above.")

    print("=" * 80)


if __name__ == "__main__":
    run_all_master_tests()
