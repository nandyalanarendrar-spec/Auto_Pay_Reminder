from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class EMIBase(BaseModel):
    loan_name: str = Field(..., example="iPhone 15 EMI")
    total_installments: int = Field(..., gt=0, example=12)
    installments_paid: Optional[int] = Field(0, ge=0, example=3)
    installment_amount: float = Field(..., gt=0, example=250.00)
    start_date: Optional[date] = None
    next_due_date: date
    remaining_amount: Optional[float] = None
    status: Optional[str] = Field("active", example="active")
    calendar_event_id: Optional[str] = None
    calendar_id: Optional[str] = "primary"
    calendar_sync_status: Optional[str] = "PENDING"
    calendar_sync_error: Optional[str] = None
    calendar_last_synced_at: Optional[datetime] = None

class EMICreate(EMIBase):
    pass

class EMIUpdate(BaseModel):
    loan_name: Optional[str] = None
    total_installments: Optional[int] = None
    installments_paid: Optional[int] = None
    installment_amount: Optional[float] = None
    start_date: Optional[date] = None
    next_due_date: Optional[date] = None
    remaining_amount: Optional[float] = None
    status: Optional[str] = None
    pay_installment: Optional[bool] = Field(False, description="Set to True to pay one installment automatically")

class EMIResponse(EMIBase):
    id: str
    user_id: str
    completion_percentage: float = 0.0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

