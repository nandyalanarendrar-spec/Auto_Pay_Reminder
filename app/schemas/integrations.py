from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date as date_type
import uuid

# OAuth Connect Response
class GoogleCalendarConnectResponse(BaseModel):
    message: str = Field(..., example="Google Calendar OAuth authorization URL generated.")
    authorization_url: str = Field(..., example="https://accounts.google.com/o/oauth2/v2/auth?...")

# OAuth Status Response
class GoogleCalendarStatusResponse(BaseModel):
    is_connected: bool = Field(..., example=True)
    connected_email: Optional[str] = Field(None, example="user@gmail.com")
    message: str = Field(..., example="Google Calendar is connected.")

# Manual Event Creation Request
class CalendarEventCreateRequest(BaseModel):
    title: str = Field(..., example="Netflix Premium Renewal")
    date: date_type = Field(..., example="2026-09-20")
    description: Optional[str] = Field("Subscription Autopay Debit ₹649.00", example="Monthly Netflix subscription renewal")
    amount: Optional[float] = Field(649.00, example=649.00)

# Event Creation Response
class CalendarEventResponse(BaseModel):
    message: str = Field(..., example="Calendar event created successfully.")
    event_id: str = Field(..., example="evt_12345")
    html_link: Optional[str] = Field(None, example="https://www.google.com/calendar/event?eid=...")
    summary: str = Field(..., example="Autopay Renewal Alert: Netflix Premium")
    start_date: date_type = Field(..., example="2026-09-20")
