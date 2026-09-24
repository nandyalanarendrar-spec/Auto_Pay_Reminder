import os
import uuid
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Body

from app.core.security import get_current_user, get_optional_current_user, get_supabase_client
from app.services.google_calendar_service import GoogleCalendarService

router = APIRouter(prefix="/personal-reminders", tags=["Personal Custom Reminders"])

# In-memory storage fallback if Supabase table is pending
_in_memory_reminders: List[Dict[str, Any]] = []

class CustomReminderCreate(BaseModel):
    title: str = Field(..., example="Electricity Bill Payment")
    notes: Optional[str] = Field(None, example="Account No: 40219812")
    due_datetime: str = Field(..., example="2026-09-25T15:30:00")
    reminder_offsets: List[int] = Field(default=[10, 30, 60, 1440], example=[10, 30, 60, 1440]) # minutes before
    sync_calendar: bool = Field(default=True)
    sync_whatsapp: bool = Field(default=True)

class CustomReminderResponse(BaseModel):
    id: str
    user_id: str
    title: str
    notes: Optional[str]
    due_datetime: str
    reminder_offsets: List[int]
    calendar_event_id: Optional[str]
    is_completed: bool
    created_at: str

def get_clean_uuid(user_id_val: Any) -> str:
    raw = str(user_id_val or "default_user").strip('"\'')
    try:
        val = uuid.UUID(raw)
        return str(val)
    except ValueError:
        return "00000000-0000-0000-0000-000000000000"

@router.get("", response_model=List[Dict[str, Any]])
def get_personal_reminders(current_user: Optional[dict] = Depends(get_optional_current_user)):
    user_id = "default_user"
    if current_user:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", "default_user")
    clean_uid = get_clean_uuid(user_id)
    
    try:
        supabase = get_supabase_client()
        if supabase:
            res = supabase.from_("personal_reminders").select("*").eq("user_id", clean_uid).order("created_at", desc=True).execute()
            if res.data:
                return res.data
    except Exception as e:
        print("Note: Supabase personal_reminders table read note:", e)

    # Fallback in-memory query
    return [r for r in _in_memory_reminders if str(r.get("user_id")) == clean_uid]

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_personal_reminder(
    data: CustomReminderCreate,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    user_id = "default_user"
    if current_user:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", "default_user")
    clean_uid = get_clean_uuid(user_id)
    reminder_id = str(uuid.uuid4())
    now_iso = datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S+05:30")

    # Sort and clean offsets (ensure unique positive integers)
    offsets = sorted(list(set([int(x) for x in data.reminder_offsets if int(x) >= 0])))
    if not offsets:
        offsets = [30]

    highest_offset = max(offsets)

    calendar_event_id = None
    if data.sync_calendar:
        try:
            # Sync to Google Calendar with highest selected offset popup override
            event_title = f"⏰ {data.title}"
            event_desc = f"Autopay Guard Personal Reminder\nTask: {data.title}\nDue: {data.due_datetime}\nNotes: {data.notes or 'None'}"
            
            # Single popup alert override set to the HIGHEST user-selected notification time
            overrides = [{"method": "popup", "minutes": highest_offset}]
            
            cal_res = GoogleCalendarService.create_custom_calendar_event(
                user_id=clean_uid,
                title=event_title,
                event_datetime=data.due_datetime,
                description=event_desc,
                reminder_overrides=overrides,
                private_props={"personal_reminder_id": reminder_id}
            )
            if isinstance(cal_res, dict):
                calendar_event_id = cal_res.get("event_id")
        except Exception as err:
            print("Google Calendar custom reminder sync note:", err)

    # Safety check: WhatsApp alert requires at least 60 minutes lead time before due_datetime
    final_sync_whatsapp = data.sync_whatsapp
    try:
        clean_due_str = str(data.due_datetime).replace("Z", "").replace(" ", "T")
        due_dt = datetime.fromisoformat(clean_due_str)
        if due_dt.tzinfo is not None:
            due_dt = due_dt.astimezone(timezone.utc).replace(tzinfo=None)
            now_compare = datetime.utcnow()
        else:
            now_compare = datetime.now()
        mins_remaining = (due_dt - now_compare).total_seconds() / 60.0
        if mins_remaining < 60:
            final_sync_whatsapp = False
    except Exception as err:
        print("Note on due_datetime parsing:", err)

    record = {
        "id": reminder_id,
        "user_id": clean_uid,
        "title": data.title,
        "notes": data.notes,
        "due_datetime": data.due_datetime,
        "reminder_offsets": offsets,
        "sync_calendar": data.sync_calendar,
        "sync_whatsapp": final_sync_whatsapp,
        "calendar_event_id": calendar_event_id,
        "is_completed": False,
        "created_at": now_iso
    }

    # Save to Supabase DB or in-memory fallback
    try:
        supabase = get_supabase_client()
        if supabase:
            supabase.from_("personal_reminders").insert(record).execute()
        else:
            _in_memory_reminders.insert(0, record)
    except Exception as e:
        print("Note: Supabase insert personal_reminders fallback to memory:", e)
        _in_memory_reminders.insert(0, record)

    return record

@router.delete("/{reminder_id}")
def delete_personal_reminder(
    reminder_id: str,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    global _in_memory_reminders
    user_id = "default_user"
    if current_user:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", "default_user")
    clean_uid = get_clean_uuid(user_id)

    old_cal_id = None
    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.from_("personal_reminders").select("calendar_event_id").eq("id", reminder_id).execute()
            if res.data:
                old_cal_id = res.data[0].get("calendar_event_id")
            supabase.from_("personal_reminders").delete().eq("id", reminder_id).execute()
        except Exception as e:
            print("Supabase delete note:", e)

    if not old_cal_id:
        for r in _in_memory_reminders:
            if r.get("id") == reminder_id:
                old_cal_id = r.get("calendar_event_id")
                break

    _in_memory_reminders = [r for r in _in_memory_reminders if not (r.get("id") == reminder_id)]

    try:
        GoogleCalendarService.delete_event_by_id_or_metadata(
            user_id=clean_uid,
            event_id=old_cal_id,
            private_props={"personal_reminder_id": reminder_id}
        )
    except Exception as err:
        print("Google Calendar event delete note:", err)

    return {"status": "SUCCESS", "message": "Personal reminder deleted."}

@router.put("/{reminder_id}", response_model=Dict[str, Any])
def update_personal_reminder(
    reminder_id: str,
    data: CustomReminderCreate,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    global _in_memory_reminders
    user_id = "default_user"
    if current_user:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", "default_user")
    clean_uid = get_clean_uuid(user_id)

    offsets = sorted(list(set([int(x) for x in data.reminder_offsets if int(x) >= 0])))
    if not offsets:
        offsets = [30]

    final_sync_whatsapp = data.sync_whatsapp
    try:
        clean_due_str = str(data.due_datetime).replace("Z", "").replace(" ", "T")
        due_dt = datetime.fromisoformat(clean_due_str)
        now_compare = datetime.now()
        mins_remaining = (due_dt - now_compare).total_seconds() / 60.0
        if mins_remaining < 60:
            final_sync_whatsapp = False
    except Exception as err:
        print("Note on due_datetime parsing in update:", err)

    highest_offset = max(offsets)

    # 1. Fetch old_cal_id from Supabase or memory and purge OLD Google Calendar event
    old_cal_id = None
    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.from_("personal_reminders").select("calendar_event_id").eq("id", reminder_id).execute()
            if res.data:
                old_cal_id = res.data[0].get("calendar_event_id")
        except Exception:
            pass

    if not old_cal_id:
        for r in _in_memory_reminders:
            if r.get("id") == reminder_id:
                old_cal_id = r.get("calendar_event_id")
                break

    try:
        GoogleCalendarService.delete_event_by_id_or_metadata(
            user_id=clean_uid,
            event_id=old_cal_id,
            private_props={"personal_reminder_id": reminder_id}
        )
    except Exception as err:
        print("Note purging old Google Calendar event before update:", err)

    # 2. Add NEW updated Google Calendar event with updated date, time, title, and highest offset
    calendar_event_id = None
    if data.sync_calendar:
        try:
            event_title = f"⏰ {data.title}"
            event_desc = f"Autopay Guard Personal Reminder\nTask: {data.title}\nDue: {data.due_datetime}\nNotes: {data.notes or 'None'}"
            overrides = [{"method": "popup", "minutes": highest_offset}]
            cal_res = GoogleCalendarService.create_custom_calendar_event(
                user_id=clean_uid,
                title=event_title,
                event_datetime=data.due_datetime,
                description=event_desc,
                reminder_overrides=overrides,
                private_props={"personal_reminder_id": reminder_id}
            )
            if isinstance(cal_res, dict):
                calendar_event_id = cal_res.get("event_id")
        except Exception as err:
            print("Google Calendar custom reminder update note:", err)

    updated_fields = {
        "title": data.title,
        "notes": data.notes,
        "due_datetime": data.due_datetime,
        "reminder_offsets": offsets,
        "sync_calendar": data.sync_calendar,
        "sync_whatsapp": final_sync_whatsapp,
        "calendar_event_id": calendar_event_id
    }

    updated_record = None
    if supabase:
        try:
            res = supabase.from_("personal_reminders").update(updated_fields).eq("id", reminder_id).execute()
            if res.data and len(res.data) > 0:
                updated_record = res.data[0]
        except Exception as e:
            print("Supabase update note:", e)

    for r in _in_memory_reminders:
        if r.get("id") == reminder_id:
            r.update(updated_fields)
            if not updated_record:
                updated_record = dict(r)
            break

    if not updated_record:
        updated_record = {
            "id": reminder_id,
            "user_id": clean_uid,
            "is_completed": False,
            "created_at": datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            **updated_fields
        }
        _in_memory_reminders.insert(0, updated_record)

    return updated_record

@router.patch("/{reminder_id}/toggle-complete", response_model=Dict[str, Any])
def toggle_complete_personal_reminder(
    reminder_id: str,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    global _in_memory_reminders
    user_id = "default_user"
    if current_user:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", "default_user")
    clean_uid = get_clean_uuid(user_id)

    current_completed = True
    cal_event_id = None
    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.from_("personal_reminders").select("is_completed, calendar_event_id").eq("id", reminder_id).execute()
            if res.data:
                current_completed = not bool(res.data[0].get("is_completed"))
                cal_event_id = res.data[0].get("calendar_event_id")
            supabase.from_("personal_reminders").update({"is_completed": current_completed}).eq("id", reminder_id).execute()
        except Exception as e:
            print("Supabase toggle completion note:", e)
    else:
        for r in _in_memory_reminders:
            if r.get("id") == reminder_id:
                current_completed = not bool(r.get("is_completed", False))
                cal_event_id = r.get("calendar_event_id")
                break

    for r in _in_memory_reminders:
        if r.get("id") == reminder_id:
            r["is_completed"] = current_completed
            break

    # If task is now COMPLETED, delete the connected event from Google Calendar
    if current_completed:
        try:
            if not cal_event_id:
                for r in _in_memory_reminders:
                    if r.get("id") == reminder_id:
                        cal_event_id = r.get("calendar_event_id")
                        break
            GoogleCalendarService.delete_event_by_id_or_metadata(
                user_id=clean_uid,
                event_id=cal_event_id,
                private_props={"personal_reminder_id": reminder_id}
            )
        except Exception as err:
            print("Delete calendar event on task complete note:", err)

    return {"status": "SUCCESS", "id": reminder_id, "is_completed": current_completed}
