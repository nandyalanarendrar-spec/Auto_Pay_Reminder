from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DeviceTokenRegisterRequest(BaseModel):
    device_token: str = Field(..., example="fcm_token_sample_1234567890_abc")
    platform: Optional[str] = Field("web", example="android")

class DeviceTokenResponse(BaseModel):
    message: str = Field(..., example="Device FCM token registered successfully.")
    user_id: str = Field(..., example="usr_12345")
    device_token: str = Field(..., example="fcm_token_sample_1234567890_abc")
    platform: str = Field(..., example="android")
    registered_at: datetime = Field(default_factory=datetime.utcnow)

class UserDevicesResponse(BaseModel):
    user_id: str = Field(..., example="usr_12345")
    count: int = Field(..., example=1)
    tokens: List[Dict[str, Any]] = Field(..., example=[{"token": "fcm_token_123", "platform": "android"}])

class PushNotificationTestRequest(BaseModel):
    title: str = Field(..., example="⚠️ Urgent Payment Due Tomorrow!")
    body: str = Field(..., example="Your Swiggy One subscription ₹149.00 will be auto-debited tomorrow.")
    data: Optional[Dict[str, str]] = Field(default={"type": "subscription_due", "id": "sub_123"})

class PushNotificationResponse(BaseModel):
    message: str = Field(..., example="Push notification sent via FCM successfully.")
    user_id: str = Field(..., example="usr_12345")
    devices_targeted: int = Field(..., example=1)
    success_count: int = Field(..., example=1)
    failure_count: int = Field(..., example=0)
    details: List[Dict[str, Any]] = Field(default=[])
