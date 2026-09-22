import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
from app.core.security import get_supabase_client

supabase = get_supabase_client()

try:
    # Query subscriptions with sim-evt- or placeholder calendar_event_id
    sub_res = supabase.from_("subscriptions").select("id, merchant_name, name, calendar_event_id, calendar_sync_status, user_id").execute()
    subs = sub_res.data or []

    placeholder_subs = [s for s in subs if str(s.get("calendar_event_id") or "").startswith("sim-")]
    real_gcal_subs = [s for s in subs if s.get("calendar_event_id") and not str(s.get("calendar_event_id")).startswith("sim-")]
    pending_subs = [s for s in subs if not s.get("calendar_event_id")]

    print("=============================================================")
    print("SUBSCRIPTION CALENDAR EVENT AUDIT REPORT")
    print("=============================================================")
    print(f"Total Subscriptions: {len(subs)}")
    print(f"  - Real Google Calendar IDs: {len(real_gcal_subs)}")
    print(f"  - Placeholder 'sim-evt-' IDs: {len(placeholder_subs)}")
    print(f"  - Pending/No Event IDs: {len(pending_subs)}")

    print("\n--- List of Placeholder 'sim-evt-' Records ---")
    for s in placeholder_subs:
        m_name = s.get("merchant_name") or s.get("name")
        print(f"  - ID: {s.get('id')} | Name: {m_name} | CalendarID: {s.get('calendar_event_id')} | Status: {s.get('calendar_sync_status')}")

    # Query EMIs
    emi_res = supabase.from_("emis").select("id, lender_name, loan_name, calendar_event_id, calendar_sync_status, user_id").execute()
    emis = emi_res.data or []
    placeholder_emis = [e for e in emis if str(e.get("calendar_event_id") or "").startswith("sim-")]
    
    print("\n=============================================================")
    print("EMI CALENDAR EVENT AUDIT REPORT")
    print("=============================================================")
    print(f"Total EMIs: {len(emis)}")
    print(f"  - Placeholder 'sim-evt-' IDs: {len(placeholder_emis)}")
    for e in placeholder_emis:
        l_name = e.get("lender_name") or e.get("loan_name")
        print(f"  - ID: {e.get('id')} | Name: {l_name} | CalendarID: {e.get('calendar_event_id')} | Status: {e.get('calendar_sync_status')}")

except Exception as err:
    print("Database query error:", err)
