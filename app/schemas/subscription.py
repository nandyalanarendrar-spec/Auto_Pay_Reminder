from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

ALLOWED_CATEGORIES = [
    "Entertainment", "Software", "Education", 
    "Gaming", "Utilities", "Other", "General"
]

class SubscriptionBase(BaseModel):
    merchant_name: str = Field(..., example="Netflix")
    category: Optional[str] = Field("General", example="Entertainment")
    amount: float = Field(..., gt=0, example=19.99)
    billing_frequency: Optional[str] = Field("monthly", example="monthly")
    start_date: Optional[date] = None
    next_payment_date: date
    status: Optional[str] = Field("active", example="active")
    is_recurring: Optional[bool] = True
    autopay_enabled: Optional[bool] = True
    trial_start_date: Optional[date] = None
    trial_end_date: Optional[date] = None
    expected_first_payment_date: Optional[date] = None
    is_free_trial: Optional[bool] = False
    risk_score: Optional[int] = Field(10, ge=1, le=100)
    receipt_url: Optional[str] = None
    source: Optional[str] = Field("user_added", example="detected")
    calendar_event_id: Optional[str] = None
    calendar_id: Optional[str] = "primary"
    calendar_sync_status: Optional[str] = "PENDING"
    calendar_sync_error: Optional[str] = None
    calendar_last_synced_at: Optional[datetime] = None

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(BaseModel):
    merchant_name: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    billing_frequency: Optional[str] = None
    start_date: Optional[date] = None
    next_payment_date: Optional[date] = None
    status: Optional[str] = None
    is_recurring: Optional[bool] = None
    autopay_enabled: Optional[bool] = None
    trial_start_date: Optional[date] = None
    trial_end_date: Optional[date] = None
    expected_first_payment_date: Optional[date] = None
    is_free_trial: Optional[bool] = None
    risk_score: Optional[int] = None
    receipt_url: Optional[str] = None

class SubscriptionResponse(SubscriptionBase):
    id: str
    user_id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

