from pydantic import BaseModel, Field
from typing import List, Optional

class ChatbotQueryRequest(BaseModel):
    query: str = Field(..., example="How do I cancel my Netflix subscription?")

class ChatbotQueryResponse(BaseModel):
    query: str = Field(..., example="How do I cancel my Netflix subscription?")
    intent_matched: bool = Field(..., example=True)
    intent_type: str = Field(..., example="cancellation_guide")
    matched_merchant: Optional[str] = Field(..., example="Netflix India")
    official_url: Optional[str] = Field(None, example="https://www.netflix.com/youraccount")
    support_contact: Optional[str] = Field(None, example="https://help.netflix.com")
    response_text: str = Field(..., example="Here are the official cancellation steps for Netflix India...")
    steps: List[str] = Field(default=[], example=[
        "1. Open netflix.com or the Netflix app and log in to your account.",
        "2. Click your Profile icon at the top-right corner and select 'Account'.",
        "3. Under 'Membership & Billing', click 'Cancel Membership'.",
        "4. Click 'Finish Cancellation' to confirm."
    ])

class ChatbotAskRequest(BaseModel):
    query: str = Field(..., example="How many payments do I have coming up this month?")

class ChatbotAskResponse(BaseModel):
    query: str
    query_type: str = Field(..., example="cancellation_guide or financial_ai")
    reply: str
    matched_intent: bool
    matched_merchant: Optional[str] = None
    cancellation_steps: List[str] = Field(default=[])
    official_url: Optional[str] = None
    support_contact: Optional[str] = None
    suggested_actions: List[str] = Field(default=[])
    context_used: dict = Field(default={})

