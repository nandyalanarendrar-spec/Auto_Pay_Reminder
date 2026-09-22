from typing import Dict, Any, Optional
from app.services.chatbot_service import ChatbotService
from app.services.ai_service import AIService

class ChatbotUpgradeService:

    @staticmethod
    def ask(user_id: str, query: str) -> Dict[str, Any]:
        """
        Module 20 Hybrid Chatbot Resolver:
        1. Step 1 (Intent Check): Check if user query matches cancellation guide intent (Module 16).
           If yes, return official cancellation steps immediately.
        2. Step 2 (LLM Financial Query): If not cancellation intent, fetch full user financial 
           context and query Gemini AI (or analytical fallback) with strict zero-hallucination rules.
        """
        clean_query = (query or "").strip()
        if not clean_query:
            return {
                "query": query,
                "query_type": "invalid",
                "reply": "Please provide a question or subscription name.",
                "matched_intent": False,
                "cancellation_steps": [],
                "official_url": None,
                "context_used": {}
            }

        # 1. Step 1: Rule-Based Cancellation Intent Match
        rule_res = ChatbotService.query(clean_query)
        if rule_res.get("intent_matched"):
            return {
                "query": clean_query,
                "query_type": "cancellation_guide",
                "reply": rule_res.get("response_text"),
                "matched_intent": True,
                "matched_merchant": rule_res.get("matched_merchant"),
                "cancellation_steps": rule_res.get("steps", []),
                "official_url": rule_res.get("official_url"),
                "support_contact": rule_res.get("support_contact"),
                "context_used": {}
            }

        # 2. Step 2: LLM Financial Query Engine (Context Ingestion + Gemini AI)
        ai_res = AIService.chat(user_id, clean_query)
        return {
            "query": clean_query,
            "query_type": "financial_ai",
            "reply": ai_res.get("response"),
            "matched_intent": False,
            "matched_merchant": None,
            "cancellation_steps": [],
            "official_url": None,
            "support_contact": None,
            "suggested_actions": ai_res.get("suggested_actions", []),
            "context_used": ai_res.get("context_summary", {})
        }
