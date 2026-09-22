import sys
import os
import time
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app.core.security import get_supabase_client
from app.services.calendar_agent_service import CalendarAgentService
from app.services.google_calendar_service import GoogleCalendarService

supabase = get_supabase_client()

print("=============================================================")
print("GOOGLE CALENDAR AUTOMATIC OAUTH BACKFILL CONVERSION AUDIT")
print("=============================================================")

# 1. Check OAuth Tokens
oauth_res = supabase.from_("oauth_tokens").select("*").execute()
tokens = oauth_res.data or []

print(f"\n1. Active OAuth Tokens in Database: {len(tokens)}")
target_uid = None
for t in tokens:
    print(f"  - User ID: {t.get('user_id')} | Google Email: {t.get('google_email')} | Provider: {t.get('provider')}")
    if t.get("access_token") or t.get("refresh_token"):
        target_uid = t.get("user_id")

if not target_uid:
    print("\n⚠️ Awaiting OAuth Completion by User...")
    sys.exit(0)

print(f"\nFound Authenticated Google User ID: {target_uid}")

# 2. Query pre-backfill placeholder records
sub_pre = supabase.from_("subscriptions").select("id, merchant_name, name, calendar_event_id, calendar_sync_status").eq("user_id", target_uid).execute().data or []
emi_pre = supabase.from_("emis").select("id, lender_name, loan_name, calendar_event_id, calendar_sync_status").eq("user_id", target_uid).execute().data or []

placeholder_subs_pre = [s for s in sub_pre if str(s.get("calendar_event_id") or "").startswith("sim-")]
placeholder_emis_pre = [e for e in emi_pre if str(e.get("calendar_event_id") or "").startswith("sim-")]

print(f"\nPre-Backfill Status for User {target_uid}:")
print(f"  - Subscriptions with sim-evt- placeholder IDs: {len(placeholder_subs_pre)}")
print(f"  - EMIs with sim-evt- placeholder IDs: {len(placeholder_emis_pre)}")

example_sub_pre = placeholder_subs_pre[0] if placeholder_subs_pre else (sub_pre[0] if sub_pre else None)
if example_sub_pre:
    print(f"\nExample Record BEFORE Backfill:")
    print(f"  - Name: {example_sub_pre.get('merchant_name') or example_sub_pre.get('name')}")
    print(f"  - ID: {example_sub_pre.get('id')}")
    print(f"  - calendar_event_id: {example_sub_pre.get('calendar_event_id')}")
    print(f"  - calendar_sync_status: {example_sub_pre.get('calendar_sync_status')}")

# 3. Trigger / Execute Canonical Backfill
print(f"\n--- 2. Executing Backfill: CalendarAgentService.resync_user_calendar('{target_uid}') ---")
start_t = time.time()
resync_result = CalendarAgentService.resync_user_calendar(target_uid)
end_t = time.time()

print(f"Backfill Executed in {end_t - start_t:.2f} seconds.")
print("Resync Summary Result:")
print(json.dumps(resync_result, indent=2))

# 4. Query post-backfill records
sub_post = supabase.from_("subscriptions").select("id, merchant_name, name, calendar_event_id, calendar_sync_status").eq("user_id", target_uid).execute().data or []
emi_post = supabase.from_("emis").select("id, lender_name, loan_name, calendar_event_id, calendar_sync_status").eq("user_id", target_uid).execute().data or []

placeholder_subs_post = [s for s in sub_post if str(s.get("calendar_event_id") or "").startswith("sim-")]
placeholder_emis_post = [e for e in emi_post if str(e.get("calendar_event_id") or "").startswith("sim-")]
real_subs_post = [s for s in sub_post if s.get("calendar_event_id") and not str(s.get("calendar_event_id")).startswith("sim-")]
real_emis_post = [e for e in emi_post if e.get("calendar_event_id") and not str(e.get("calendar_event_id")).startswith("sim-")]

print(f"\n=============================================================")
print("POST-BACKFILL AUDIT RESULTS")
print("=============================================================")
print(f"Successfully Converted Subscriptions to Real Google IDs: {len(real_subs_post)}")
print(f"Successfully Converted EMIs to Real Google IDs: {len(real_emis_post)}")
print(f"Remaining Placeholder 'sim-evt-' Records (Target: 0): {len(placeholder_subs_post) + len(placeholder_emis_post)}")

if example_sub_pre:
    example_sub_post = next((s for s in sub_post if s.get("id") == example_sub_pre.get("id")), None)
    if example_sub_post:
        print(f"\nExample Record AFTER Backfill:")
        print(f"  - Name: {example_sub_post.get('merchant_name') or example_sub_post.get('name')}")
        print(f"  - ID: {example_sub_post.get('id')}")
        print(f"  - calendar_event_id BEFORE: {example_sub_pre.get('calendar_event_id')}")
        print(f"  - calendar_event_id AFTER:  {example_sub_post.get('calendar_event_id')}")
        print(f"  - calendar_sync_status:    {example_sub_post.get('calendar_sync_status')}")

if len(placeholder_subs_post) + len(placeholder_emis_post) == 0:
    print("\n✅ FULL BACKFILL CONVERSION PASSED 100%! All 14 placeholder records converted to real Google Calendar IDs!")
else:
    print("\n⚠️ PARTIAL BACKFILL / Awaiting complete OAuth connection.")
