import sys
import os
import urllib.request
import json
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app.core.security import get_supabase_client
from app.services.calendar_agent_service import CalendarAgentService
from app.services.google_calendar_service import GoogleCalendarService

supabase = get_supabase_client()

print("=============================================================")
print("LIVE OAUTH BACKFILL CONVERSION & GCAL API VERIFICATION")
print("=============================================================")

# 1. Fetch connected OAuth Tokens
tokens_res = supabase.from_("oauth_tokens").select("*").execute()
tokens = tokens_res.data or []

print(f"\n--- OAuth Tokens in Supabase Database ({len(tokens)} records) ---")
target_user_id = None
google_email = None

for t in tokens:
    print(f"  - User ID: {t.get('user_id')} | Google Email: {t.get('google_email')} | Provider: {t.get('provider')}")
    if t.get("access_token") or t.get("refresh_token"):
        target_user_id = t.get("user_id")
        google_email = t.get("google_email")

if not target_user_id:
    # Check subscriptions table for active user_id
    all_subs = supabase.from_("subscriptions").select("user_id").execute().data or []
    if all_subs:
        target_user_id = all_subs[0].get("user_id")

print(f"\nTargeting User ID: {target_user_id} ({google_email})")

# STEP 1: Query pre-backfill placeholder records (sim-evt-%)
print("\n--- STEP 1: Pre-Backfill Database Audit (WHERE calendar_event_id LIKE 'sim-evt-%') ---")

subs_pre = supabase.from_("subscriptions").select("id, merchant_name, name, calendar_event_id, calendar_sync_status").eq("user_id", target_user_id).execute().data or []
emis_pre = supabase.from_("emis").select("id, lender_name, loan_name, calendar_event_id, calendar_sync_status").eq("user_id", target_user_id).execute().data or []

placeholder_subs_pre = [s for s in subs_pre if str(s.get("calendar_event_id") or "").startswith("sim-")]
placeholder_emis_pre = [e for e in emis_pre if str(e.get("calendar_event_id") or "").startswith("sim-")]

print(f"Subscriptions with 'sim-evt-%' placeholders: {len(placeholder_subs_pre)} (out of {len(subs_pre)} total)")
print("Raw Subscriptions Placeholder Rows:")
print(json.dumps(placeholder_subs_pre, indent=2))

print(f"\nEMIs with 'sim-evt-%' placeholders: {len(placeholder_emis_pre)} (out of {len(emis_pre)} total)")
print("Raw EMIs Placeholder Rows:")
print(json.dumps(placeholder_emis_pre, indent=2))

example_pre = placeholder_subs_pre[0] if placeholder_subs_pre else (subs_pre[0] if subs_pre else None)

# STEP 2: Manually trigger / execute CalendarAgentService.resync_user_calendar
print("\n--- STEP 2: Executing CalendarAgentService.resync_user_calendar ---")
resync_start = time.time()
resync_res = CalendarAgentService.resync_user_calendar(target_user_id)
resync_end = time.time()

print(f"Resync Execution Time: {resync_end - resync_start:.2f} seconds")
print("Raw Resync Result Summary:")
print(json.dumps(resync_res, indent=2))

# STEP 3: Re-run audit query after backfill
print("\n--- STEP 3: Post-Backfill Database Audit (WHERE calendar_event_id LIKE 'sim-evt-%') ---")
subs_post = supabase.from_("subscriptions").select("id, merchant_name, name, calendar_event_id, calendar_sync_status").eq("user_id", target_user_id).execute().data or []
emis_post = supabase.from_("emis").select("id, lender_name, loan_name, calendar_event_id, calendar_sync_status").eq("user_id", target_user_id).execute().data or []

placeholder_subs_post = [s for s in subs_post if str(s.get("calendar_event_id") or "").startswith("sim-")]
placeholder_emis_post = [e for e in emis_post if str(e.get("calendar_event_id") or "").startswith("sim-")]

print(f"Post-Backfill Subscriptions with 'sim-evt-%': {len(placeholder_subs_post)} (Expected: 0)")
print("Raw Post-Backfill Subscriptions Placeholder Rows:")
print(json.dumps(placeholder_subs_post, indent=2))

print(f"Post-Backfill EMIs with 'sim-evt-%': {len(placeholder_emis_post)} (Expected: 0)")
print("Raw Post-Backfill EMIs Placeholder Rows:")
print(json.dumps(placeholder_emis_post, indent=2))

# STEP 4: Pick example record and show BEFORE and AFTER side by side
print("\n--- STEP 4: Side-by-Side Example Comparison ---")
if example_pre:
    ex_id = example_pre.get("id")
    example_post = next((s for s in subs_post if s.get("id") == ex_id), None)
    
    print(f"Record Name:            {example_pre.get('merchant_name') or example_pre.get('name')}")
    print(f"Record ID:              {ex_id}")
    print(f"calendar_event_id BEFORE: {example_pre.get('calendar_event_id')}")
    print(f"calendar_event_id AFTER:  {example_post.get('calendar_event_id') if example_post else 'N/A'}")
    print(f"calendar_sync_status:   {example_post.get('calendar_sync_status') if example_post else 'N/A'}")

    target_gcal_id = example_post.get("calendar_event_id") if example_post else None

    # STEP 5: Direct Google Calendar API GET Verification
    if target_gcal_id and not str(target_gcal_id).startswith("sim-"):
        print(f"\n--- STEP 5: Calling Google Calendar API GET /events/{target_gcal_id} ---")
        access_token = GoogleCalendarService.get_valid_access_token(target_user_id)
        if access_token:
            get_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{target_gcal_id}"
            req = urllib.request.Request(get_url, headers={"Authorization": f"Bearer {access_token}"})
            try:
                with urllib.request.urlopen(req) as resp:
                    google_data = json.loads(resp.read().decode("utf-8"))
                print("✅ RAW GOOGLE CALENDAR API RESPONSE (HTTP 200 OK):")
                print(json.dumps(google_data, indent=2))
            except Exception as err:
                print("Google API GET error:", err)
        else:
            print("Access token not available for user.")

print("\n=============================================================")
print("✅ BACKFILL CONVERSION & DIRECT GOOGLE API VERIFICATION COMPLETE!")
print("=============================================================")
