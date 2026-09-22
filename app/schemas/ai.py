from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AIChatRequest(BaseModel):
    message: str = Field(..., example="How can I save ₹2,000 on my monthly subscriptions?")

class AIChatResponse(BaseModel):
    query: str = Field(..., example="How can I save ₹2,000 on my monthly subscriptions?")
    response: str = Field(..., example="Based on your active subscriptions, you can save ₹2,148.00 by cancelling unused trials...")
    context_summary: Dict[str, Any] = Field(..., example={
        "monthly_subscriptions_total": 4230.00,
        "monthly_emis_total": 12500.00,
        "safety_score": 75
    })
    suggested_actions: List[str] = Field(default=[], example=[
        "Cancel Adobe Creative Cloud (₹3,165.20/mo)",
        "Review Swiggy One auto-renewal"
    ])
