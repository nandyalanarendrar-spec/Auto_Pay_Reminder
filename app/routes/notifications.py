from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Optional
from app.core.security import get_current_user
from app.schemas.notifications import (
    DeviceTokenRegisterRequest,
    DeviceTokenResponse,
    UserDevicesResponse,
    PushNotificationTestRequest,
    PushNotificationResponse
)
from app.services.firebase_notification_service import FirebaseNotificationService
from app.services.notification_log_service import NotificationLogService

router = APIRouter(prefix="/notifications", tags=["Push Notifications (FCM) & Reminders"])

@router.post(
    "/register-device",
    response_model=DeviceTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register FCM device token for current user"
)
def register_device(
    payload: DeviceTokenRegisterRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Registers a Firebase Cloud Messaging (FCM) device token for the authenticated user.
    A user can have multiple registered device tokens (web, mobile, tablet).
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    res = FirebaseNotificationService.register_device_token(
        user_id=user_id,
        device_token=payload.device_token,
        platform=payload.platform or "web"
    )
    return {
        "message": "FCM Device token registered successfully for push notifications.",
        "user_id": res["user_id"],
        "device_token": res["device_token"],
        "platform": res["platform"],
        "registered_at": res["registered_at"]
    }

@router.get(
    "/devices",
    response_model=UserDevicesResponse,
    summary="List all registered FCM device tokens for current user"
)
def list_user_devices(
    current_user: dict = Depends(get_current_user)
):
    """
    Returns a list of active FCM device tokens registered for the logged-in user.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    tokens = FirebaseNotificationService.get_user_devices(user_id)
    return {
        "user_id": user_id,
        "count": len(tokens),
        "tokens": tokens
    }

@router.post(
    "/send-test",
    response_model=PushNotificationResponse,
    summary="Send an instant test push notification via FCM"
)
def send_test_notification(
    payload: PushNotificationTestRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Sends an instant push notification via Firebase Cloud Messaging to all devices registered for the user.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    res = FirebaseNotificationService.send_push_notification(
        user_id=user_id,
        title=payload.title,
        body=payload.body,
        data=payload.data
    )
    return res

@router.post(
    "/trigger-daily-job",
    summary="Run automated daily payment reminder scanner job"
)
def trigger_daily_reminder_job(
    current_user: dict = Depends(get_current_user)
):
    """
    Manually triggers the daily background scanner job that scans upcoming subscriptions/EMIs
    due in the next 7 days and dispatches urgent push notifications.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    res = FirebaseNotificationService.run_daily_payment_reminder_job(user_id=user_id)
    return res


@router.get(
    "/due-reminders",
    summary="Get upcoming payment reminders needing notification for current user"
)
def get_due_reminders(
    current_user: dict = Depends(get_current_user)
):
    """
    Returns subscriptions and EMIs due in 7, 3, 1, or 0 days for the logged-in user
    that HAVE NOT been logged as notified yet today in the backend database.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    alerts = FirebaseNotificationService.get_due_reminders_for_user(user_id)
    return {
        "user_id": user_id,
        "count": len(alerts),
        "due_alerts": alerts
    }


@router.post(
    "/mark-notified",
    summary="Record sent notification in backend database"
)
def mark_notification_sent(
    payload: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Logs a notification displayed by the browser/app into the backend notification_logs DB table.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    entity_type = payload.get("entity_type") or payload.get("type") or "subscription"
    entity_id = payload.get("entity_id") or payload.get("id")
    notification_type = payload.get("notification_type") or "1d"

    if not entity_id:
        raise HTTPException(status_code=400, detail="entity_id is required")

    log_entry = NotificationLogService.log_notification(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=str(entity_id),
        notification_type=notification_type,
        channel="web"
    )

    return {
        "status": "success",
        "message": "Notification log recorded in database.",
        "log": log_entry
    }


