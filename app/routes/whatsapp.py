from fastapi import APIRouter, Depends, status, HTTPException
from typing import Optional
from pydantic import BaseModel
from app.core.security import get_current_user, get_supabase_client
from app.core.config import settings
from app.services.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Meta Cloud API Reminders"])

class WhatsAppTestRequest(BaseModel):
    phone_number: Optional[str] = None

class WhatsAppReminderRequest(BaseModel):
    phone_number: Optional[str] = None
    merchant_name: str
    amount: float
    due_date: str
    days_left: int = 1
    is_free_trial: bool = False

def resolve_user_phone(current_user: dict, explicit_phone: Optional[str] = None) -> str:
    """
    Dynamically resolves user's registered phone number from user_metadata, database profile, or payload.
    """
    if explicit_phone and len(explicit_phone.strip()) >= 10:
        return explicit_phone.strip()

    user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
    metadata = current_user.get("user_metadata", {}) if isinstance(current_user, dict) else {}

    phone = metadata.get("phone_number") or metadata.get("phone")
    if phone:
        return str(phone)

    # Database lookup fallback
    if user_id:
        try:
            supabase = get_supabase_client()
            res = supabase.from_("users").select("phone_number").eq("id", user_id).execute()
            if res.data and res.data[0].get("phone_number"):
                return str(res.data[0]["phone_number"])
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No registered mobile number found for WhatsApp alerts. Please enter your mobile number in your profile."
    )

@router.get(
    "/status",
    summary="Check WhatsApp Meta Cloud API configuration status"
)
def get_whatsapp_status(current_user: dict = Depends(get_current_user)):
    """
    Returns Meta WhatsApp Cloud API credentials configuration status.
    """
    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "") or ""
    access_token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "") or ""
    business_phone = getattr(settings, "WHATSAPP_BUSINESS_PHONE_NUMBER", "15551911379") or "15551911379"

    is_configured = bool(phone_number_id and access_token)
    return {
        "whatsapp_configured": is_configured,
        "mode": "LIVE_META_CLOUD_API" if is_configured else "SIMULATION_MODE",
        "phone_number_id": phone_number_id[:6] + "..." if phone_number_id else "Not Set",
        "business_phone_number": business_phone,
        "access_token_set": bool(access_token)
    }

@router.post(
    "/send-test",
    summary="Send test WhatsApp alert message"
)
def send_test_whatsapp(
    payload: WhatsAppTestRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Dispatches a test WhatsApp notification to verify Meta WhatsApp Cloud API integration.
    Dynamically targets the logged-in user's registered mobile number.
    """
    metadata = current_user.get("user_metadata") or {} if isinstance(current_user, dict) else {}
    target_phone = resolve_user_phone(current_user, payload.phone_number)
    user_name = metadata.get("name") or metadata.get("full_name") or "User"

    res = WhatsAppService.send_test_message(to_phone=target_phone, user_name=user_name)
    return res

@router.post(
    "/send-reminder",
    summary="Send custom WhatsApp payment alert"
)
def send_whatsapp_reminder(
    payload: WhatsAppReminderRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Dispatches an instant WhatsApp payment or trial expiry alert for a specific subscription/EMI.
    Dynamically targets the logged-in user's registered mobile number.
    """
    metadata = current_user.get("user_metadata") or {} if isinstance(current_user, dict) else {}
    target_phone = resolve_user_phone(current_user, payload.phone_number)
    user_name = metadata.get("name") or metadata.get("full_name") or "User"

    res = WhatsAppService.send_payment_reminder(
        to_phone=target_phone,
        user_name=user_name,
        item_name=payload.merchant_name,
        amount=payload.amount,
        due_date=payload.due_date,
        days_left=payload.days_left,
        is_trial=payload.is_free_trial
    )
    return res
