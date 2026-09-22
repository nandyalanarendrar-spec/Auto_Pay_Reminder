from fastapi import APIRouter, Depends, status
from app.core.security import get_current_user
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["Gemini AI Financial Assistant"])

@router.post(
    "/chat",
    response_model=AIChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Interactive context-aware Gemini AI financial advisor"
)
def chat_with_ai(
    payload: AIChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Conversational AI financial assistant powered by Gemini AI.
    Automatically injects current user's live active subscriptions, EMIs, safety score, and upcoming debits.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    res = AIService.chat(user_id=user_id, message=payload.message)
    return res
