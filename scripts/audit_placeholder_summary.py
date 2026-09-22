import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
from app.core.security import get_supabase_client

supabase = get_supabase_client()

try:
    sub_res = supabase.from_("subscriptions").select("id, merchant_name, name, calendar_event_id, calendar_sync_status, user_id").execute()
    subs = sub_res.data or []

    placeholder_subs = [s for s in subs if str(s.get("calendar_event_id") or "").startswith("sim-")]
    real_subs = [s for s in subs if s.get("calendar_event_id") and not str(s.get("calendar_event_id")).startswith("sim-")]
    pending_subs = [s for s in subs if not s.get("calendar_event_id")]

    emi_res = supabase.from_("emis").select("id, lender_name, loan_name, calendar_event_id, calendar_sync_status, user_id").execute()
    emis = emi_res.data or []
    placeholder_emis = [e for e in emis if str(e.get("calendar_event_id") or "").startswith("sim-")]
    real_emis = [e for e in emis if e.get("calendar_event_id") and not str(e.get("calendar_event_id")).startswith("sim-")]
    pending_emis = [e for e in emis if not e.get("calendar_event_id")]

    print("=============================================================")
    print("CALENDAR EVENT IDENTIFIER AUDIT SUMMARY")
    print("=============================================================")
    print(f"Subscriptions Total: {len(subs)}")
    print(f"  - Real Google Calendar IDs: {len(real_subs)}")
    print(f"  - Placeholder 'sim-evt-' IDs: {len(placeholder_subs)}")
    print(f"  - Unsynced / Pending IDs: {len(pending_subs)}")

    print(f"\nEMIs Total: {len(emis)}")
    print(f"  - Real Google Calendar IDs: {len(real_emis)}")
    print(f"  - Placeholder 'sim-evt-' IDs: {len(placeholder_emis)}")
    print(f"  - Unsynced / Pending IDs: {len(pending_emis)}")

    total_affected = len(placeholder_subs) + len(placeholder_emis)
    print(f"\nTotal Records Awaiting Real Google OAuth Backfill: {total_affected}")

except Exception as err:
    print("Audit error:", err)
