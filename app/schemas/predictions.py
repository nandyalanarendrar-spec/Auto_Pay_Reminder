from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
import uuid

# Single Subscription Countdown Response
class SubscriptionCountdownResponse(BaseModel):
    subscription_id: uuid.UUID = Field(..., example="3fa85f64-5717-4562-b3fc-2c963f66afa6")
    merchant_name: str = Field(..., example="Netflix Premium")
    expected_amount: float = Field(..., example=649.00)
    billing_frequency: str = Field(..., example="monthly")
    expected_date: date = Field(..., example="2026-09-20")
    days_left: int = Field(..., example=6)
    urgency_level: str = Field(..., example="upcoming", description="normal, upcoming, prepare, tomorrow, due_today, overdue")
    urgency_icon: str = Field(..., example="🟡")
    autopay_enabled: bool = Field(True)

# Unified Item for Upcoming Subscriptions + EMIs
class UpcomingPaymentItem(BaseModel):
    item_type: str = Field(..., example="subscription", description="subscription or emi")
    id: str = Field(..., example="sub-123")
    name: str = Field(..., example="Netflix Premium")
    category: str = Field(..., example="Entertainment")
    amount: float = Field(..., example=649.00)
    frequency_or_loan: str = Field(..., example="monthly")
    next_date: date = Field(..., example="2026-09-20")
    days_left: int = Field(..., example=6)
    urgency_level: str = Field(..., example="upcoming")
    urgency_icon: str = Field(..., example="🟡")
    autopay_enabled: bool = Field(True)
    status: str = Field(..., example="active")

# Combined Response for Dashboard Upcoming Payments
class UpcomingPaymentsResponse(BaseModel):
    message: str
    user_id: uuid.UUID
    total_count: int
    upcoming_payments: List[UpcomingPaymentItem]

# N-Day Financial Cashflow Forecast Response
class FinancialForecastResponse(BaseModel):
    message: str
    user_id: uuid.UUID
    forecast_days: int = Field(30, example=30)
    total_forecast_amount: float = Field(..., example=12847.00)
    subscription_total: float = Field(..., example=6147.00)
    emi_total: float = Field(..., example=6700.00)
    item_count: int = Field(..., example=5)
    items: List[UpcomingPaymentItem]

# Item for contributing risk factor
class SafetyScoreFactor(BaseModel):
    factor_name: str = Field(..., example="Free Trial Auto-Conversion")
    impact_points: int = Field(..., example=-25, description="Negative deduction points from score")
    severity: str = Field(..., example="high", description="high, medium, low")
    description: str = Field(..., example="Notion AI free trial converts to paid debit in 1 day")

# Overall Financial Safety Score Response (0-100)
class FinancialSafetyScoreResponse(BaseModel):
    message: str
    user_id: uuid.UUID
    safety_score: int = Field(..., example=85, description="Composite score out of 100")
    status_grade: str = Field(..., example="EXCELLENT", description="EXCELLENT, GOOD, MODERATE_RISK, HIGH_RISK")
    status_icon: str = Field(..., example="🟢", description="🟢, 🟡, 🟠, 🔴")
    summary: str = Field(..., example="Your subscription finances are highly secure.")
    deductions_total: int = Field(..., example=15)
    contributing_factors: List[SafetyScoreFactor]
