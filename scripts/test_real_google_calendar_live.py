import sys
import os
import urllib.request
import urllib.error
import json
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app.services.google_calendar_service import GoogleCalendarService
from app.services.subscription_service import SubscriptionService
from app.core.security import get_supabase_client

supabase = get_supabase_client()

print("=============================================================")
print("LIVE GOOGLE CALENDAR API VERIFICATION & AUDIT")
print("=============================================================")

# 1. Check existing OAuth token records in database
oauth_res = supabase.from_("oauth_tokens").select("*").execute()
print(f"\n1. Found {len(oauth_res.data or [])} Google OAuth connection token records in Supabase DB:")
target_user_id = None
target_email = None

for tok in (oauth_res.data or []):
    print(f"  - User ID: {tok.get('user_id')} | Google Email: {tok.get('google_email')} | Provider: {tok.get('provider')}")
    if tok.get("access_token") or tok.get("refresh_token"):
        target_user_id = tok.get("user_id")
        target_email = tok.get("google_email")

if not target_user_id:
    print("No OAuth token found. Testing token refresh / OAuth resolution.")
    target_user_id = "b214d765-ddd1-4dab-b44a-0162fca19579"

print(f"\nTargeting Authenticated User ID: {target_user_id} ({target_email})")

# 2. Get valid access token for target user
access_token = GoogleCalendarService.get_valid_access_token(target_user_id)
print(f"Valid Access Token Retrieved from Google OAuth: {bool(access_token)}")

if access_token:
    print(f"Access Token Snippet: {access_token[:25]}...")

    # 3. Create a test event DIRECTLY on Google Calendar API
    print("\n--- STEP 3: Posting Live Event directly to Google Calendar API (https://www.googleapis.com/calendar/v3/...) ---")
    event_payload = {
        "summary": "🔴 Live Google API Audit Test — Netflix ₹649",
        "description": "Live API Verification Test for Autopay Guard System",
        "start": {"dateTime": "2026-10-15T09:00:00+05:30", "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": "2026-10-15T10:00:00+05:30", "timeZone": "Asia/Kolkata"},
        "extendedProperties": {
            "private": {
                "source": "autopay_guard",
                "user_id": str(target_user_id),
                "entity_type": "subscription",
                "test": "live_audit"
            }
        }
    }

    calendar_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    req = urllib.request.Request(
        calendar_url,
        data=json.dumps(event_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            google_create_data = json.loads(resp.read().decode("utf-8"))
        
        real_gcal_id = google_create_data.get("id")
        print("✅ LIVE GOOGLE CALENDAR API CREATE RESPONSE:")
        print(f"  - Real Google Event ID (from response['id']): {real_gcal_id}")
        print(f"  - HTML Link: {google_create_data.get('htmlLink')}")
        print(f"  - Status: {google_create_data.get('status')}")
        print(f"  - Summary: {google_create_data.get('summary')}")

        # 4. Perform direct GET from Google's servers to verify event exists on Google Calendar
        print(f"\n--- STEP 4: Calling Google's GET /events/{real_gcal_id} to Verify Live Presence ---")
        get_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{real_gcal_id}"
        get_req = urllib.request.Request(get_url, headers={"Authorization": f"Bearer {access_token}"})
        
        with urllib.request.urlopen(get_req) as get_resp:
            google_get_data = json.loads(get_resp.read().decode("utf-8"))

        print("✅ LIVE GOOGLE CALENDAR GET RESPONSE:")
        print(f"  - ID: {google_get_data.get('id')}")
        print(f"  - Summary: {google_get_data.get('summary')}")
        print(f"  - Start: {google_get_data.get('start')}")
        print(f"  - Status: {google_get_data.get('status')}")

        # 5. Call DELETE on Google's servers directly
        print(f"\n--- STEP 5: Calling Google's DELETE /events/{real_gcal_id} ---")
        del_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{real_gcal_id}"
        del_req = urllib.request.Request(del_url, headers={"Authorization": f"Bearer {access_token}"}, method="DELETE")
        
        with urllib.request.urlopen(del_req) as del_resp:
            print(f"Google DELETE HTTP Status: {del_resp.status}")

        # 6. Verify HTTP 404 / 410 from Google after deletion
        print(f"\n--- STEP 6: Calling Google's GET /events/{real_gcal_id} After Delete to Confirm HTTP 404 / 410 ---")
        try:
            with urllib.request.urlopen(get_req) as post_del_resp:
                post_data = json.loads(post_del_resp.read().decode("utf-8"))
                print(f"Post-delete Google GET status: {post_data.get('status')}")
        except urllib.error.HTTPError as http_err:
            print(f"✅ GOOGLE API HTTP RESPONSE: {http_err.code} {http_err.reason}")
            print(f"   (HTTP {http_err.code} confirms event was permanently deleted from Google's servers!)")

    except urllib.error.HTTPError as err:
        print("Google API Error:", err.code, err.reason, err.read().decode('utf-8', errors='ignore'))
else:
    print("User has not authorized Google OAuth yet (or token requires re-auth).")
