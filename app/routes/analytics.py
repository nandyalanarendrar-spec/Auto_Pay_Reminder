from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from fastapi import Query
from app.schemas.analytics import (
    RecurringDetectionRequest, 
    RecurringDetectionSummaryResponse,
    EMIDetectionSummaryResponse,
    AnomalySummaryResponse,
    SpendingSummaryResponse,
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
    BudgetStatusResponse
)
from app.services.recurring_detector_service import RecurringDetectorService
from app.services.emi_detector_service import EMIDetectorService
from app.services.anomaly_detector_service import AnomalyDetectorService
from app.services.spending_analytics_service import SpendingAnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics & Intelligence"])

@router.post(
    "/detect-recurring",
    response_model=RecurringDetectionSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect recurring payment subscriptions from raw transaction history"
)
def detect_recurring_payments(
    payload: Optional[RecurringDetectionRequest] = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload is None:
        payload = RecurringDetectionRequest()
    """
    Analyzes raw bank transactions for the logged-in user to detect repeating subscription patterns.
    
    - **amount_tolerance_pct**: Allowable variation in amount (e.g. 0.10 for 10%)
    - **monthly_date_tolerance_days**: Max gap deviation in days for monthly cycles (default 3)
    - **yearly_date_tolerance_days**: Max gap deviation in days for yearly cycles (default 10)
    - **auto_create_subscriptions**: Auto-creates `Subscription` records with status='pending_confirmation'
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        results = RecurringDetectorService.detect_recurring_payments(
            db=db,
            user_id=user_id,
            amount_tolerance_pct=payload.amount_tolerance_pct or 0.10,
            monthly_date_tolerance_days=payload.monthly_date_tolerance_days or 3,
            yearly_date_tolerance_days=payload.yearly_date_tolerance_days or 10,
            auto_create_subscriptions=payload.auto_create_subscriptions if payload.auto_create_subscriptions is not None else True
        )
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute recurring detection algorithm: {str(e)}"
        )

@router.post(
    "/detect-emi",
    response_model=EMIDetectionSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect loan & device financing EMIs from bank transaction narrations"
)
def detect_emi_payments(
    current_user: User = Depends(get_current_user)
):
    """
    Scans transaction narrations for EMI keywords (EMI, INSTALLMENT, NACH, ECS, LOAN)
    and extracts fraction installment counts (e.g. 3/12) to auto-populate EMI records.
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        results = EMIDetectorService.detect_emis(user_id=user_id)
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute EMI detection algorithm: {str(e)}"
        )

@router.get(
    "/anomalies",
    response_model=AnomalySummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect financial anomalies (price hikes, unknown debits, duplicate categories)"
)
def get_financial_anomalies(
    price_hike_threshold_pct: Optional[float] = Query(0.15, description="Threshold percentage for price hike detection (default 0.15 for 15%)"),
    current_user: User = Depends(get_current_user)
):
    """
    Scans user transactions and subscriptions for financial anomalies:
    1. **price_increase** (🔴 High): Price increased by >15% compared to historical average.
    2. **unknown_merchant** (🟠 Medium): Debit from unrecognized or suspicious merchant name.
    3. **possible_duplicate** (🟡 Low): 2+ active subscriptions in the same category.
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        results = AnomalyDetectorService.detect_anomalies(
            user_id=user_id,
            price_hike_threshold_pct=price_hike_threshold_pct or 0.15
        )
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute anomaly detection engine: {str(e)}"
        )

@router.get(
    "/spending-summary",
    response_model=SpendingSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get monthly & annual spending totals and category breakdown"
)
def get_spending_summary(
    current_user: User = Depends(get_current_user)
):
    """
    Computes total monthly spend, annual projected spend, and category-wise percentage distribution.
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        return SpendingAnalyticsService.get_spending_summary(user_id=user_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute spending summary: {str(e)}"
        )

@router.post(
    "/what-if",
    response_model=WhatIfSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate subscription cancellations and calculate instant rupee savings"
)
def simulate_cancellation(
    payload: WhatIfSimulationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Simulates cancelling selected subscription IDs and calculates instant monthly & annual rupee savings.
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        return SpendingAnalyticsService.simulate_what_if_cancellation(
            user_id=user_id,
            cancel_subscription_ids=payload.cancel_subscription_ids
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run what-if cancellation simulation: {str(e)}"
        )

@router.get(
    "/budget-status",
    response_model=BudgetStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get budget utilization status against a monthly cap"
)
def get_budget_status(
    monthly_budget: Optional[float] = Query(15000.0, description="Monthly budget cap in INR (default ₹15,000.00)"),
    current_user: User = Depends(get_current_user)
):
    """
    Compares current total monthly spend against monthly budget cap and calculates remaining budget & utilization %.
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        return SpendingAnalyticsService.get_budget_status(
            user_id=user_id,
            monthly_budget=monthly_budget or 15000.0
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute budget status: {str(e)}"
        )
