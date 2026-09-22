from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from decimal import Decimal
import uuid

# Request schema to customize detection thresholds optionally
class RecurringDetectionRequest(BaseModel):
    amount_tolerance_pct: Optional[float] = Field(default=0.10, description="Tolerance percentage for amount variation (e.g. 0.10 for 10%)")
    monthly_date_tolerance_days: Optional[int] = Field(default=3, description="Tolerance days for monthly cycle gap")
    yearly_date_tolerance_days: Optional[int] = Field(default=10, description="Tolerance days for yearly cycle gap")
    auto_create_subscriptions: Optional[bool] = Field(default=True, description="Whether to auto-create Subscription records with status 'pending_confirmation'")

# Item schema for each detected recurring subscription pattern
class DetectedSubscriptionItem(BaseModel):
    subscription_id: Optional[uuid.UUID] = None
    merchant_name: str = Field(..., example="Netflix Premium")
    category: str = Field(..., example="Entertainment")
    expected_amount: float = Field(..., example=649.00, description="Expected average recurring debit amount in INR")
    billing_frequency: str = Field(..., example="monthly")
    confidence_score: int = Field(..., example=95)
    first_transaction_date: date
    last_transaction_date: date
    next_payment_date: date
    matching_transactions_count: int = Field(..., example=6)
    status: str = Field(..., example="pending_confirmation")

# Summary response schema returned by the recurring detection endpoint
class RecurringDetectionSummaryResponse(BaseModel):
    message: str
    user_id: uuid.UUID
    detected_count: int
    updated_transactions_count: int
    detected_subscriptions: List[DetectedSubscriptionItem]

# Item schema for each detected EMI loan pattern
class DetectedEMIItem(BaseModel):
    emi_id: Optional[uuid.UUID] = None
    loan_name: str = Field(..., example="iPhone 15 HDFC EMI")
    installment_amount: float = Field(..., example=4500.00)
    total_installments: int = Field(..., example=12)
    installments_paid: int = Field(..., example=3)
    completion_percentage: float = Field(..., example=25.0)
    remaining_amount: float = Field(..., example=40500.00)
    next_due_date: date
    matching_transactions_count: int = Field(..., example=3)
    status: str = Field(..., example="active")

# Summary response schema returned by the EMI detection endpoint
class EMIDetectionSummaryResponse(BaseModel):
    message: str
    user_id: uuid.UUID
    detected_count: int
    updated_transactions_count: int
    detected_emis: List[DetectedEMIItem]

# Item schema for each detected financial anomaly
class AnomalyItem(BaseModel):
    id: str = Field(..., example="anom-123")
    anomaly_type: str = Field(..., example="price_increase", description="price_increase, unknown_merchant, possible_duplicate")
    merchant_name: str = Field(..., example="Adobe Creative Cloud")
    category: str = Field(..., example="Design & SaaS")
    severity: str = Field(..., example="high", description="high, medium, low")
    severity_icon: str = Field(..., example="🔴", description="🔴, 🟠, 🟡")
    description: str = Field(..., example="Price increased by 30% from ₹3,299 to ₹4,230")
    old_amount: Optional[float] = Field(None, example=3299.00)
    new_amount: Optional[float] = Field(None, example=4230.00)
    percentage_increase: Optional[float] = Field(None, example=28.22)

# Summary response schema returned by the anomaly detection endpoint
class AnomalySummaryResponse(BaseModel):
    message: str
    user_id: uuid.UUID
    total_anomalies: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    anomalies: List[AnomalyItem]

# Category Breakdown Item for Spending Summary
class CategoryBreakdownItem(BaseModel):
    category: str = Field(..., example="Entertainment")
    monthly_amount: float = Field(..., example=828.00)
    percentage_of_total: float = Field(..., example=12.5)
    item_count: int = Field(..., example=2)

# Spending Summary Response
class SpendingSummaryResponse(BaseModel):
    message: str
    user_id: uuid.UUID
    total_monthly_spend: float = Field(..., example=6626.00)
    total_yearly_projected: float = Field(..., example=79512.00)
    active_subscriptions_count: int = Field(..., example=5)
    active_emis_count: int = Field(..., example=2)
    category_breakdown: List[CategoryBreakdownItem]

# Request Schema for What-If Calculator Simulation
class WhatIfSimulationRequest(BaseModel):
    cancel_subscription_ids: List[str] = Field(..., example=["sub-1", "sub-5"], description="List of subscription IDs to simulate cancelling")

# Response Schema for What-If Calculator Simulation
class WhatIfSimulationResponse(BaseModel):
    message: str
    user_id: uuid.UUID
    current_monthly_total: float = Field(..., example=6626.00)
    after_cancel_monthly_total: float = Field(..., example=1747.00)
    monthly_savings: float = Field(..., example=4879.00)
    yearly_savings: float = Field(..., example=58548.00)
    percentage_saved: float = Field(..., example=73.63)
    cancelled_items: List[dict]

# Budget Status Response
class BudgetStatusResponse(BaseModel):
    message: str
    user_id: uuid.UUID
    monthly_budget: float = Field(..., example=15000.00)
    current_monthly_spend: float = Field(..., example=6626.00)
    budget_remaining: float = Field(..., example=8374.00)
    is_over_budget: bool = Field(False)
    over_budget_amount: float = Field(0.0, example=0.0)
    budget_utilization_pct: float = Field(..., example=44.17)
    status_message: str = Field(..., example="Under budget! You have ₹8,374.00 remaining.")
