from pydantic import BaseModel, Field
from typing import Optional

class MockGenerateRequest(BaseModel):
    months: Optional[int] = Field(6, ge=1, le=24, example=6)
    include_emi: Optional[bool] = Field(True, example=True)
    include_anomaly: Optional[bool] = Field(False, example=False)
