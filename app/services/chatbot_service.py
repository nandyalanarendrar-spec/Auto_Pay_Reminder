import os
import json
from typing import Dict, Any, Optional, List

KB_FILE = "cancellation_knowledge_base.json"

def _load_knowledge_base() -> Dict[str, Any]:
    if os.path.exists(KB_FILE):
        try:
            with open(KB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Error reading cancellation knowledge base:", e)
            return {}
    return {}

CANCELLATION_KEYWORDS = [
    "cancel", "cancellation", "stop", "unsubscribe", "end", "delete",
    "deactivate", "remove", "close", "how to cancel", "how do i cancel"
]

class ChatbotService:

    @staticmethod
    def query(user_query: str) -> Dict[str, Any]:
        """
        Rule-based intent and merchant matching engine.
        Never invents steps — strictly matches query against verified knowledge base.
        """
        q_lower = user_query.lower().strip()
        kb = _load_knowledge_base()

        # Step 1: Detect cancellation intent
        is_cancel_intent = any(keyword in q_lower for keyword in CANCELLATION_KEYWORDS)

        # Step 2: Search for matching merchant in knowledge base
        matched_key = None
        matched_entry = None

        for key, entry in kb.items():
            aliases = entry.get("aliases", [])
            merchant_name = entry.get("merchant_name", "").lower()
            
            # Match aliases or merchant name
            if any(alias in q_lower for alias in aliases) or merchant_name in q_lower:
                matched_key = key
                matched_entry = entry
                break

        # Step 3: Format output response (only when cancellation intent is explicitly detected)
        if is_cancel_intent and matched_entry:
            merchant_name = matched_entry.get("merchant_name")
            official_url = matched_entry.get("official_url")
            support_contact = matched_entry.get("support_contact")
            steps = matched_entry.get("steps", [])

            steps_formatted = "\n".join(steps)
            response_text = f"Here are the official, step-by-step cancellation instructions for **{merchant_name}**:\n\n{steps_formatted}\n\n🔗 Official Manage URL: {official_url}\n📞 Support Contact: {support_contact}"

            return {
                "query": user_query,
                "intent_matched": True,
                "intent_type": "cancellation_guide",
                "matched_merchant": merchant_name,
                "official_url": official_url,
                "support_contact": support_contact,
                "response_text": response_text,
                "steps": steps
            }

        # Fallback response when merchant or intent is not found
        fallback_text = (
            "I could not find cancellation instructions for that specific service in my verified knowledge base.\n\n"
            "I currently support step-by-step cancellation guides for: Netflix, Spotify, Amazon Prime, Disney+ Hotstar, "
            "YouTube Premium, Swiggy One, Zomato Gold, JioCinema, SonyLIV, ZEE5, Apple Music/iCloud, and Airtel Black."
        )

        return {
            "query": user_query,
            "intent_matched": False,
            "intent_type": "unknown",
            "matched_merchant": None,
            "official_url": None,
            "support_contact": None,
            "response_text": fallback_text,
            "steps": []
        }
