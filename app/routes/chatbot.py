from fastapi import APIRouter, Depends, status
from app.core.security import get_current_user
from app.schemas.chatbot import ChatbotQueryRequest, ChatbotQueryResponse, ChatbotAskRequest, ChatbotAskResponse
from app.services.chatbot_service import ChatbotService
from app.services.chatbot_upgrade_service import ChatbotUpgradeService

router = APIRouter(prefix="/chatbot", tags=["Rule-Based & LLM Financial Assistant"])

@router.post(
    "/query",
    response_model=ChatbotQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query rule-based cancellation guide chatbot (Legacy Endpoint)"
)
def query_chatbot(
    payload: ChatbotQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Rule-based chatbot endpoint for subscription cancellation guidance.
    Performs pure keyword matching against verified Indian subscription knowledge base.
    Never invents steps.
    """
    res = ChatbotService.query(payload.query)
    return res


@router.post(
    "/ask",
    response_model=ChatbotAskResponse,
    status_code=status.HTTP_200_OK,
    summary="Natural Language Financial Chatbot & Cancellation Assistant (Module 20)"
)
def ask_chatbot(
    payload: ChatbotAskRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Module 20 Upgraded Hybrid Chatbot Endpoint.
    - If user asks for cancellation instructions (e.g., 'How to cancel Netflix'), returns verified cancellation steps.
    - If user asks natural language financial questions (e.g., 'this week how many payments'), ingests user's active
      subscriptions, EMIs, safety score, and forecast, and passes it to Gemini AI with zero-hallucination constraints.
    """
    user_id = current_user.get("id") or current_user.get("sub", "user_123")
    res = ChatbotUpgradeService.ask(user_id, payload.query)
    return res
