from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
from app.core.security import get_current_user
from app.schemas.mock_data import MockGenerateRequest
from app.services.mock_generator_service import MockGeneratorService

router = APIRouter(prefix="/mock", tags=["Mock Data Generator (Testing Only)"])

@router.post("/generate-transactions", response_model=dict, status_code=status.HTTP_201_CREATED)
def generate_transactions(
    payload: MockGenerateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generates realistic raw bank transactions (noise + recurring subscriptions + EMIs + price hikes + anomalies).
    All generated transactions remain UNLABELED (`is_labeled_recurring=False`), simulating raw bank statement data
    ready for future detection algorithms to process!
    """
    txns = MockGeneratorService.generate_mock_dataset(
        user_id=current_user["id"],
        months=payload.months or 6,
        include_emi=payload.include_emi if payload.include_emi is not None else True,
        include_anomaly=payload.include_anomaly if payload.include_anomaly is not None else False
    )

    return {
        "message": f"Successfully generated {len(txns)} realistic bank transactions for {payload.months} months!",
        "user_id": current_user["id"],
        "total_generated": len(txns),
        "sample_transactions": txns[:5]
    }

@router.get("/transactions", response_model=dict)
def get_user_transactions(current_user: dict = Depends(get_current_user)):
    """
    Retrieves raw bank statement transactions for the logged-in user.
    """
    txns = MockGeneratorService.get_user_transactions(current_user["id"])
    return {
        "user_id": current_user["id"],
        "count": len(txns),
        "transactions": txns
    }
