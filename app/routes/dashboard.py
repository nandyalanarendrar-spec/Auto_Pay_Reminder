from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from app.core.security import get_current_user
from app.schemas.predictions import (
    SubscriptionCountdownResponse,
    UpcomingPaymentsResponse,
    FinancialForecastResponse,
    FinancialSafetyScoreResponse
)
from app.services.prediction_service import PredictionService
from app.services.safety_score_service import SafetyScoreService

router = APIRouter(tags=["Dashboard & Predictions"])

@router.get(
    "/subscriptions/{subscription_id}/next-payment",
    response_model=SubscriptionCountdownResponse,
    summary="Get next payment countdown and urgency for a specific subscription"
)
def get_subscription_next_payment(
    subscription_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Returns days_left, urgency_level (normal, upcoming 🟡, prepare 🟠, tomorrow 🔴, due_today 🚨),
    urgency_icon, expected_date, and expected_amount for a specific subscription.
    Auto-advances passed dates.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    result = PredictionService.get_subscription_countdown(user_id, subscription_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found or access denied."
        )
    return result

@router.get(
    "/dashboard/upcoming-payments",
    response_model=UpcomingPaymentsResponse,
    summary="Get combined upcoming subscriptions and EMIs sorted by days_left"
)
def get_dashboard_upcoming_payments(
    current_user: dict = Depends(get_current_user)
):
    """
    Returns ALL upcoming subscriptions + EMIs for the current user, combined into one list,
    sorted by days_left ascending with urgency indicators.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    return PredictionService.get_upcoming_payments(user_id)

@router.get(
    "/dashboard/forecast",
    response_model=FinancialForecastResponse,
    summary="Get N-day financial cashflow forecast summing upcoming subscriptions & EMIs"
)
def get_dashboard_financial_forecast(
    days: Optional[int] = Query(30, description="Number of days to forecast (default 30)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Sums up total expected payments (subscriptions + EMIs) falling within the next N days.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    return PredictionService.get_financial_forecast(user_id, days=days or 30)

@router.get(
    "/dashboard/safety-score",
    response_model=FinancialSafetyScoreResponse,
    summary="Get composite Financial Safety Risk Score (0-100) with factor breakdown"
)
def get_dashboard_safety_score(
    current_user: dict = Depends(get_current_user)
):
    """
    Calculates composite Financial Safety Risk Score (0-100) evaluating trial traps,
    price hikes, unknown debits, duplicate categories, and imminent large payments.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    return SafetyScoreService.get_user_safety_score(user_id)
