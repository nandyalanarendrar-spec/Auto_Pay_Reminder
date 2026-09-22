import urllib.request
import urllib.parse
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from typing import Optional

from app.core.security import get_current_user, get_optional_current_user
from app.schemas.integrations import (
    GoogleCalendarConnectResponse,
    GoogleCalendarStatusResponse,
    CalendarEventCreateRequest,
    CalendarEventResponse
)
from app.services.google_calendar_service import GoogleCalendarService

router = APIRouter(prefix="/integrations/google-calendar", tags=["Integrations & Calendar"])

@router.post(
    "/connect",
    response_model=GoogleCalendarConnectResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Google OAuth2 authorization URL for Google Calendar connection"
)
def connect_google_calendar(
    current_user: dict = Depends(get_current_user)
):
    """
    Generates official Google OAuth2 consent URL requesting `https://www.googleapis.com/auth/calendar.events` scope with login_hint.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", "default_user")
    user_email = current_user.get("email") if isinstance(current_user, dict) else getattr(current_user, "email", None)
    
    auth_url = GoogleCalendarService.get_authorization_url(user_id=user_id, user_email=user_email)
    return {
        "message": "Google Calendar OAuth authorization URL generated. Open this URL in browser to connect your account.",
        "authorization_url": auth_url
    }

@router.get(
    "/callback",
    response_class=HTMLResponse,
    summary="Handle Google OAuth2 redirect callback"
)
def google_calendar_oauth_callback(
    code: str = Query(..., description="Authorization code returned by Google"),
    state: Optional[str] = Query(None, description="User ID state parameter")
):
    """
    Handles Google OAuth2 redirect, exchanges authorization code for tokens, and verifies email match.
    """
    try:
        res = GoogleCalendarService.handle_oauth_callback(code=code, state=state)
        
        if not res.get("success"):
            expected = res.get("expected_email", "your registered account")
            authorized = res.get("google_email", "another account")
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Autopay Guard - Account Mismatch Error</title>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #080F1F; color: #fff; text-align: center; padding: 50px; }}
                    .card {{ background: rgba(30, 15, 25, 0.95); border: 1px solid rgba(244,63,94,0.4); border-radius: 24px; padding: 40px; max-width: 520px; margin: 0 auto; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }}
                    h1 {{ color: #F43F5E; font-size: 22px; margin-bottom: 12px; }}
                    p {{ color: #CBD5E1; font-size: 14px; line-height: 1.6; }}
                    .badge {{ background: #1E293B; border: 1px solid #475569; padding: 3px 8px; border-radius: 6px; font-family: monospace; color: #38BDF8; font-weight: bold; }}
                    .badge-rose {{ background: #4C0519; border: 1px solid #9F1239; padding: 3px 8px; border-radius: 6px; font-family: monospace; color: #FDA4AF; font-weight: bold; }}
                    .btn {{ display: inline-block; margin-top: 25px; background: #E11D48; color: white; padding: 12px 24px; border-radius: 12px; text-decoration: none; font-weight: bold; font-size: 13px; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>⚠️ Account Email Mismatch</h1>
                    <p>You registered in AutoPay Guard with <span class="badge">{expected}</span>, but selected Google account <span class="badge-rose">{authorized}</span>.</p>
                    <p style="margin-top:15px; font-size:13px; color:#94A3B8;">To ensure calendar security and exact sync, please authorize using your registered email address.</p>
                    <a href="#" onclick="window.close()" class="btn">Close & Try Again</a>
                </div>
            </body>
            </html>
            """

        google_email = res.get("google_email", "Google Account")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Autopay Guard - Google Calendar Connected</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #080F1F; color: #fff; text-align: center; padding: 50px; }}
                .card {{ background: rgba(18, 25, 43, 0.9); border: 1px solid rgba(16,185,129,0.3); border-radius: 24px; padding: 40px; max-width: 500px; margin: 0 auto; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }}
                h1 {{ color: #10B981; font-size: 24px; margin-bottom: 10px; }}
                p {{ color: #94A3B8; font-size: 14px; line-height: 1.6; }}
                .badge {{ background: #064E3B; border: 1px solid #059669; padding: 4px 10px; border-radius: 8px; font-family: monospace; color: #A7F3D0; font-weight: bold; }}
                .btn {{ display: inline-block; margin-top: 20px; background: #10B981; color: white; padding: 12px 24px; border-radius: 12px; text-decoration: none; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>✅ Google Calendar Connected!</h1>
                <p>Connected Google Account: <span class="badge">{google_email}</span></p>
                <p style="margin-top:10px;">Your subscription renewals & EMI debits will now automatically sync to your calendar with reminder alerts.</p>
                <a href="#" onclick="window.close()" class="btn">Close Window</a>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return f"<h2>OAuth Error</h2><p>{str(e)}</p>"

@router.get(
    "/status",
    response_model=GoogleCalendarStatusResponse,
    summary="Check Google Calendar connection status for current user"
)
def get_google_calendar_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Returns boolean status indicating if Google Calendar is connected for the user.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    user_email = current_user.get("email") if isinstance(current_user, dict) else None
    connected = GoogleCalendarService.is_connected(user_id, user_email=user_email)
    connected_email = GoogleCalendarService.get_connected_email(user_id, user_email=user_email)
    return {
        "is_connected": connected,
        "connected_email": connected_email,
        "message": "Google Calendar is connected and active." if connected else "Google Calendar is not connected."
    }

@router.post(
    "/disconnect",
    summary="Disconnect Google Calendar for current user"
)
def disconnect_google_calendar(
    current_user: dict = Depends(get_current_user)
):
    """
    Clears OAuth tokens and disconnects Google Calendar authorization.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    res = GoogleCalendarService.disconnect(user_id)
    return res

@router.post(
    "/sync",
    summary="Re-synchronize all user active subscriptions & EMIs with Google Calendar"
)
def resync_google_calendar(
    current_user: dict = Depends(get_optional_current_user)
):
    """
    Idempotent re-synchronization service (POST /calendar/sync):
    Scans active subscriptions & EMIs, checks calendar_event_ids, creates missing events, updates changed events, and purges obsolete events.
    """
    from app.services.calendar_agent_service import CalendarAgentService
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    res = CalendarAgentService.resync_user_calendar(user_id)
    return res

@router.post(
    "/sync-event",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom renewal reminder event on Google Calendar"
)
def sync_calendar_event(
    payload: CalendarEventCreateRequest,
    current_user: dict = Depends(get_optional_current_user)
):
    """
    Creates a subscription renewal or EMI payment reminder event on Google Calendar.
    """
@router.post(
    "/debug-purge",
    summary="Purge all calendar events and return detailed diagnostic logs"
)
def debug_purge_calendar(
    current_user: dict = Depends(get_optional_current_user)
):
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    access_token = GoogleCalendarService.get_valid_access_token(user_id)
    if not access_token:
        return {"error": "No access token"}

    page_token = None
    all_events = []
    
    while True:
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events?maxResults=250"
        if page_token:
            url += f"&pageToken={urllib.parse.quote(page_token)}"
        
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
        try:
            with urllib.request.urlopen(req) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
            items = res_data.get("items", [])
            all_events.extend(items)
            page_token = res_data.get("nextPageToken")
            if not page_token:
                break
        except Exception as e:
            break

    print(f"\n==========================================")
    print(f"DEBUG PURGE TRIGGERED for user: {user_id}")
    print(f"Total events found on Google Calendar: {len(all_events)}")
    
    results = []
    for item in all_events:
        summary = item.get("summary", "")
        description = item.get("description", "")
        event_id = item.get("id")
        status = item.get("status")

        if status == "cancelled":
            continue

        del_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{urllib.parse.quote(str(event_id))}"
        del_req = urllib.request.Request(del_url, headers={"Authorization": f"Bearer {access_token}"}, method="DELETE")
        try:
            with urllib.request.urlopen(del_req) as del_resp:
                print(f"  ✅ DELETED: '{summary}' ({event_id}) -> HTTP {del_resp.status}")
                results.append({"summary": summary, "id": event_id, "result": "DELETED", "code": del_resp.status})
        except urllib.error.HTTPError as he:
            print(f"  ❌ HTTP ERROR on '{summary}' ({event_id}): {he.code} {he.reason}")
            results.append({"summary": summary, "id": event_id, "result": "ERROR", "code": he.code, "reason": he.reason})
        except Exception as ex:
            print(f"  ❌ EXCEPTION on '{summary}' ({event_id}): {ex}")
            results.append({"summary": summary, "id": event_id, "result": "ERROR", "error": str(str(ex))})

    print(f"DEBUG PURGE COMPLETE: {len(results)} items processed.")
    print(f"==========================================\n")

    # Clear stored calendar_event_ids in DB and execute fresh resync
    try:
        from app.core.security import get_supabase_client
        from app.services.calendar_agent_service import CalendarAgentService
        supabase = get_supabase_client()
        clean_uid = str(user_id).strip('"\'')
        supabase.from_("subscriptions").update({"calendar_event_id": None, "calendar_sync_status": "PENDING"}).eq("user_id", clean_uid).execute()
        supabase.from_("emis").update({"calendar_event_id": None, "calendar_sync_status": "PENDING"}).eq("user_id", clean_uid).execute()
        
        sync_res = CalendarAgentService.resync_user_calendar(clean_uid)
        return {"total_purged": len(results), "purge_results": results, "resync_summary": sync_res}
    except Exception as sync_e:
        print("Debug purge resync error:", sync_e)
        return {"total_purged": len(results), "purge_results": results, "error": str(sync_e)}


@router.post(
    "/retry-failed",
    response_model=dict,
    summary="Retry all failed Google Calendar syncs for subscriptions and EMIs"
)
def retry_all_failed_calendar_syncs(
    current_user: dict = Depends(get_optional_current_user)
):
    from app.services.calendar_agent_service import CalendarAgentService
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    res = CalendarAgentService.retry_all_failed_syncs(user_id)
    return res

