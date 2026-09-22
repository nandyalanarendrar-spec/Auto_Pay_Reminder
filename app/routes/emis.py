from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Optional
from app.core.security import get_current_user
from app.schemas.emi import EMICreate, EMIUpdate, EMIResponse
from app.services.emi_service import EMIService
from app.services.google_calendar_service import GoogleCalendarService
from app.services.calendar_agent_service import CalendarAgentService
from datetime import date

router = APIRouter(prefix="/emis", tags=["EMIs & Loans"])

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_emi(payload: EMICreate, current_user: dict = Depends(get_current_user)):
    """
    Creates a new EMI loan record scoped to the logged-in user.
    Auto-computes remaining_amount and completion_percentage.
    Auto-syncs payment event to Google Calendar automatically.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    result = EMIService.create_emi(user_id, payload)

    return {
        "message": "EMI loan record created successfully",
        "emi": result,
        "calendar_sync": result.get("calendar_sync_status", "SYNCED")
    }


@router.get("/", response_model=dict)
def list_emis(current_user: dict = Depends(get_current_user)):
    """
    Lists all EMI records for the current user with computed completion_percentage.
    Auto-sweeps and rolls forward any overdue due dates first.
    """
    try:
        EMIService.auto_rollover_overdue_emis(current_user["id"])
    except Exception as e:
        print("Auto-rollover on list_emis error:", e)

    emis = EMIService.get_user_emis(current_user["id"])
    return {
        "user_id": current_user["id"],
        "count": len(emis),
        "emis": emis
    }

@router.get("/{emi_id}", response_model=dict)
def get_emi(emi_id: str, current_user: dict = Depends(get_current_user)):
    """
    Retrieves a single EMI record by ID for the logged-in user.
    """
    item = EMIService.get_emi_by_id(current_user["id"], emi_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="EMI record not found or access denied."
        )
    return {"emi": item}

@router.put("/{emi_id}", response_model=dict)
@router.patch("/{emi_id}", response_model=dict)
def update_emi(
    emi_id: str,
    payload: EMIUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Updates EMI record and auto-syncs Google Calendar. 
    Pass `pay_installment: true` to automatically pay 1 installment, increment `installments_paid`,
    deduct from `remaining_amount`, and advance `next_due_date` by 30 days!
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    item = EMIService.update_emi(user_id, emi_id, payload)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="EMI record not found or update failed."
        )

    return {
        "message": "EMI record updated successfully",
        "emi": item
    }

@router.delete("/{emi_id}", response_model=dict)
def delete_emi(emi_id: str, current_user: dict = Depends(get_current_user)):
    """
    Soft-deletes an EMI record by setting status='cancelled' and auto-removes Google Calendar event.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    item = EMIService.soft_delete_emi(user_id, emi_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="EMI record not found or cancellation failed."
        )

    return {
        "message": "EMI record cancelled successfully (soft-deleted)",
        "emi": item
    }

@router.post("/{emi_id}/retry-sync", response_model=dict)
def retry_emi_sync(emi_id: str, current_user: dict = Depends(get_current_user)):
    """
    Retries Google Calendar sync for a specific EMI loan record.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    res = CalendarAgentService.retry_emi_sync(user_id, emi_id)
    return {
        "message": "Calendar sync retry completed",
        "result": res
    }


