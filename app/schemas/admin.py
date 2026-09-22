from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AdminStatsResponse(BaseModel):
    message: str = Field(..., example="System aggregate stats retrieved successfully.")
    total_users: int = Field(..., example=42)
    total_active_subscriptions: int = Field(..., example=128)
    total_emis: int = Field(..., example=34)
    total_detected_trials: int = Field(..., example=15)
    total_high_risk_flags: int = Field(..., example=6)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class SystemHealthResponse(BaseModel):
    status: str = Field(..., example="HEALTHY")
    api_version: str = Field(..., example="1.0.0")
    api_error_rate_pct: float = Field(..., example=0.12)
    uptime_seconds: float = Field(..., example=12450.5)
    background_jobs: List[Dict[str, Any]] = Field(..., example=[
        {"name": "FCM Daily Payment Reminders Engine", "status": "ACTIVE", "frequency": "Daily"},
        {"name": "Google Calendar Sync Service", "status": "ACTIVE", "type": "Real-time"},
        {"name": "Anomaly Risk Detection Engine", "status": "ACTIVE", "type": "On-demand"}
    ])
    checked_at: datetime = Field(default_factory=datetime.utcnow)
