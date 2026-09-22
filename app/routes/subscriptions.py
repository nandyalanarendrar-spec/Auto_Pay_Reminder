from fastapi import APIRouter, Depends, status, HTTPException, Query
from typing import List, Optional
from app.core.security import get_current_user
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
from app.services.subscription_service import SubscriptionService
from app.services.google_calendar_service import GoogleCalendarService
from app.services.calendar_agent_service import CalendarAgentService
from datetime import date

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_subscription(payload: SubscriptionCreate, current_user: dict = Depends(get_current_user)):
    """
    Creates a new subscription scoped to the authenticated user.
    Auto-syncs event to Google Calendar automatically.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    result = SubscriptionService.create_subscription(None, user_id, payload)
    
    return {
        "message": "Subscription created successfully",
        "subscription": result,
        "calendar_sync": result.get("calendar_sync_status", "SYNCED")
    }


@router.get("/", response_model=dict)
def list_subscriptions(
    status: Optional[str] = Query(None, description="Filter by status: active, cancelled, trial"),
    category: Optional[str] = Query(None, description="Filter by category: Entertainment, Software, Utilities, etc."),
    current_user: dict = Depends(get_current_user)
):
    """
    Lists all subscriptions belonging to the authenticated user.
    Auto-sweeps and rolls forward any overdue payment dates / expired trials first.
    """
    try:
        SubscriptionService.auto_rollover_overdue_subscriptions(current_user["id"])
    except Exception as e:
        print("Auto-rollover on list_subscriptions error:", e)

    subs = SubscriptionService.get_user_subscriptions(current_user["id"], status=status, category=category)
    return {
        "user_id": current_user["id"],
        "count": len(subs),
        "subscriptions": subs
    }

@router.get("/{subscription_id}", response_model=dict)
def get_subscription(subscription_id: str, current_user: dict = Depends(get_current_user)):
    """
    Retrieves a single subscription by ID for the logged-in user.
    Returns HTTP 404 if subscription does not exist or belongs to another user.
    """
    sub = SubscriptionService.get_subscription_by_id(current_user["id"], subscription_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found or access denied."
        )
    return {"subscription": sub}

@router.put("/{subscription_id}", response_model=dict)
@router.patch("/{subscription_id}", response_model=dict)
def update_subscription(
    subscription_id: str,
    payload: SubscriptionUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Updates an existing subscription for the logged-in user and auto-syncs Google Calendar.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    sub = SubscriptionService.update_subscription(user_id, subscription_id, payload)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found or update failed."
        )

    return {
        "message": "Subscription updated successfully",
        "subscription": sub
    }

@router.delete("/{subscription_id}", response_model=dict)
def delete_subscription(subscription_id: str, current_user: dict = Depends(get_current_user)):
    """
    Permanently deletes a subscription from database and auto-removes Google Calendar event.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    SubscriptionService.delete_subscription(user_id, subscription_id)

    return {
        "message": "Subscription deleted successfully",
        "subscription_id": subscription_id
    }

@router.post("/{subscription_id}/retry-sync", response_model=dict)
def retry_subscription_sync(subscription_id: str, current_user: dict = Depends(get_current_user)):
    """
    Retries Google Calendar sync for a specific subscription.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    res = CalendarAgentService.retry_subscription_sync(user_id, subscription_id)
    return {
        "message": "Calendar sync retry completed",
        "result": res
    }

@router.post("/process-trials", response_model=dict)
def process_trial_conversions(current_user: dict = Depends(get_current_user)):
    """
    Scans and transitions expired free trials to paid active recurring subscriptions,
    updating the calendar event in-place.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    converted = SubscriptionService.process_trial_conversions(user_id=user_id)
    return {
        "message": f"Processed trial conversions: {len(converted)} transitioned to paid.",
        "converted_count": len(converted),
        "converted_subscriptions": converted
    }





