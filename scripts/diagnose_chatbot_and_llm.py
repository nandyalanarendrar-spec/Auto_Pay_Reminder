"""
================================================================================
🔍 DIAGNOSTIC AUDIT: CHATBOT ROUTING & LLM API INTEGRATION
================================================================================
"""
import sys
import os
import json
import urllib.request
import urllib.error

# Ensure project root is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.services.chatbot_service import ChatbotService
from app.services.chatbot_upgrade_service import ChatbotUpgradeService
from app.services.ai_service import AIService
from app.services.subscription_service import SubscriptionService
from app.services.emi_service import EMIService
from app.services.safety_score_service import SafetyScoreService
from app.services.prediction_service import PredictionService
from app.core.security import get_supabase_client


def run_diagnostics():
    print("=" * 80)
    print("🔍 CHATBOT & LLM DIAGNOSTIC AUDIT REPORT")
    print("=" * 80)

    supabase = get_supabase_client()
    try:
        res = supabase.from_("subscriptions").select("user_id").limit(1).execute()
        test_user_id = res.data[0]["user_id"] if res.data else "e5c779c4-8e67-4b1e-8927-d65f4b37e059"
    except Exception:
        test_user_id = "e5c779c4-8e67-4b1e-8927-d65f4b37e059"

    # -------------------------------------------------------------------------
    # ITEM 1: ROUTING LOGIC AUDIT FOR POST /chatbot/ask
    # -------------------------------------------------------------------------
    print("\n--- [ITEM 1] INTENT ROUTER CODE PATH TRACE ---")
    print("Code Path:")
    print("  1. POST /api/v1/chatbot/ask -> app/routes/chatbot.py:ask_chatbot()")
    print("  2. -> ChatbotUpgradeService.ask(user_id, query) in app/services/chatbot_upgrade_service.py")
    print("  3. -> ChatbotService.query(clean_query) in app/services/chatbot_service.py")
    print("     - Step 1: computes is_cancel_intent = any(keyword in q_lower...)")
    print("     - Step 2: searches kb entries for matched_entry (merchant name / alias match)")
    print("     - Step 3: IF matched_entry IS NOT NONE -> returns intent_matched = True!")
    print("       ⚠️ DEFECT DETECTED: is_cancel_intent is NEVER evaluated in Step 3!")
    print("       ANY query containing a merchant name in KB (e.g. 'Netflix', 'Spotify')")
    print("       is immediately hijacked by the cancellation guide, even for non-cancellation questions!")

    # -------------------------------------------------------------------------
    # ITEM 2: ROUTER TESTING WITH DIFFERENT QUESTIONS
    # -------------------------------------------------------------------------
    print("\n--- [ITEM 2] ROUTER INTERCEPTION TEST ---")

    test_queries = [
        ("Explicit Cancellation Query", "How to cancel Netflix?"),
        ("Merchant Question (Non-cancellation)", "When is my Netflix payment due?"),
        ("General Non-cancellation Question", "how many payments do I have this week?")
    ]

    for label, q in test_queries:
        print(f"\nTesting Query: '{q}' ({label})")
        rule_res = ChatbotService.query(q)
        print(f"  • ChatbotService.query() output:")
        print(f"    - intent_matched: {rule_res.get('intent_matched')}")
        print(f"    - intent_type: {rule_res.get('intent_type')}")
        print(f"    - matched_merchant: {rule_res.get('matched_merchant')}")

        ask_res = ChatbotUpgradeService.ask(test_user_id, q)
        print(f"  • ChatbotUpgradeService.ask() output:")
        print(f"    - query_type: {ask_res.get('query_type')}")
        print(f"    - reply snippet: {ask_res.get('reply')[:120]}...")

    # -------------------------------------------------------------------------
    # ITEM 3: DIRECT GEMINI LLM API KEY AUDIT
    # -------------------------------------------------------------------------
    print("\n--- [ITEM 3] RAW GEMINI LLM API KEY AUDIT ---")
    api_key = getattr(settings, "GEMINI_API_KEY", "") or os.getenv("VITE_GEMINI_API_KEY", "")
    print(f"Configured VITE_GEMINI_API_KEY in settings / .env:")
    print(f"  • Raw Key Length: {len(api_key)}")
    print(f"  • Raw Key Prefix: {api_key[:12]}...")
    print(f"  • Key Format Check: Starts with 'AIzaSy' ? {api_key.startswith('AIzaSy')}")

    if not api_key:
        print("  ❌ RESULT: API key is completely EMPTY!")
    else:
        # Test direct call to Gemini API bypassing app code
        print("\nSending raw HTTP request directly to Google Gemini API endpoint...")
        models_to_test = [
            "gemini-1.5-flash",
            "gemini-2.0-flash",
            "gemini-pro"
        ]

        for model in models_to_test:
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": "Reply with 'API WORKING' if you can read this."}]}]
            }
            req_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(gemini_url, data=req_bytes, headers={"Content-Type": "application/json"})

            try:
                with urllib.request.urlopen(req) as resp:
                    raw_resp = resp.read().decode("utf-8")
                    resp_json = json.loads(raw_resp)
                    print(f"  ✅ Model '{model}' Call Success! HTTP Status: {resp.status}")
                    print(f"     Raw Response: {json.dumps(resp_json, indent=2)}")
            except urllib.error.HTTPError as http_err:
                err_body = http_err.read().decode("utf-8")
                print(f"  ❌ Model '{model}' HTTP Error {http_err.code}: {http_err.reason}")
                print(f"     Raw Error Response Body: {err_body}")
            except Exception as e:
                print(f"  ❌ Model '{model}' Exception: {e}")

    # -------------------------------------------------------------------------
    # ITEM 4 & 5: USER CONTEXT INGESTION & RAW LLM REQUEST/RESPONSE AUDIT
    # -------------------------------------------------------------------------
    print("\n--- [ITEM 4 & 5] USER CONTEXT INGESTION & PROMPT INSPECTION ---")
    
    # Get test user from Supabase
    supabase = get_supabase_client()
    try:
        res = supabase.from_("subscriptions").select("user_id").limit(1).execute()
        test_user_id = res.data[0]["user_id"] if res.data else "b214d765-ddd1-4dab-b44a-0162fca19579"
    except Exception:
        test_user_id = "b214d765-ddd1-4dab-b44a-0162fca19579"

    print(f"Testing with active user ID: {test_user_id}")

    # Inspect raw context fetched by SubscriptionService, EMIService, etc.
    subs = SubscriptionService.get_user_subscriptions(test_user_id, status="active")
    emis = EMIService.get_user_emis(test_user_id)
    emis = [e for e in emis if e.get("status") != "cancelled"]
    safety_res = SafetyScoreService.get_user_safety_score(test_user_id)
    upcoming_res = PredictionService.get_upcoming_payments(test_user_id)
    upcoming = upcoming_res.get("upcoming_payments", [])

    print("\nRaw Data Fetched from DB Services:")
    print(f"  • Subscriptions ({len(subs)} items):")
    for s in subs[:3]:
        print(f"    - DB Record keys: {list(s.keys())}")
        print(f"    - s.get('name'): {s.get('name')} | s.get('merchant_name'): {s.get('merchant_name')}")

    print(f"  • EMIs ({len(emis)} items):")
    for e in emis[:3]:
        print(f"    - DB Record keys: {list(e.keys())}")
        print(f"    - e.get('lender_name'): {e.get('lender_name')} | e.get('loan_name'): {e.get('loan_name')} | e.get('merchant_name'): {e.get('merchant_name')}")

    print(f"  • Upcoming Payments ({len(upcoming)} items):")
    for u in upcoming[:3]:
        print(f"    - DB Record keys: {list(u.keys())}")
        print(f"    - u.get('title'): {u.get('title')} | u.get('merchant_name'): {u.get('merchant_name')}")

    # Check how AIService formats the prompt with these dicts
    monthly_subs = sum(float(s.get("amount", 0)) for s in subs)
    monthly_emis = sum(float(e.get("installment_amount") or e.get("monthly_installment", 0)) for e in emis)
    safety_score = safety_res.get("safety_score", 70)
    status_grade = safety_res.get("status_grade", "MODERATE_RISK")

    # In AIService.chat:
    subs_text_as_coded = ", ".join([f"{s.get('merchant_name') or s.get('name')} (₹{float(s.get('amount',0)):,.2f}/{s.get('billing_frequency') or s.get('billing_cycle','monthly')})" for s in subs]) or "None"
    emis_text_as_coded = ", ".join([f"{e.get('loan_name') or e.get('merchant_name') or e.get('lender_name')} (₹{float(e.get('installment_amount') or e.get('monthly_installment',0)):,.2f}/mo)" for e in emis]) or "None"
    upcoming_text_as_coded = ", ".join([f"{u.get('name') or u.get('title')} (₹{float(u.get('amount',0)):,.2f} on {u.get('next_date') or u.get('date')})" for u in upcoming[:5]]) or "None"

    print("\nPrompt Text Strings Formatted by AIService.chat (Current Code):")
    print(f"  • subs_text:     '{subs_text_as_coded}'")
    print(f"  • emis_text:     '{emis_text_as_coded}'")
    print(f"  • upcoming_text: '{upcoming_text_as_coded}'")

    system_prompt_generated = f"""
You are Autopay Guard AI, a smart personal financial advisor in India.
Current User Financial Profile (Amounts in Indian Rupees - ₹):
- Active Subscriptions ({len(subs)}): {subs_text_as_coded} (Total: ₹{monthly_subs:,.2f}/mo)
- Active EMIs ({len(emis)}): {emis_text_as_coded} (Total: ₹{monthly_emis:,.2f}/mo)
- Total Monthly Outflow: ₹{monthly_subs + monthly_emis:,.2f}
- Financial Safety Risk Score: {safety_score}/100 ({status_grade})
- Upcoming Debits (Next 30 Days): {upcoming_text_as_coded}

User Question: "how many payments do I have this week?"

Provide a concise, direct, helpful, and encouraging answer in Indian Rupees (₹).
Suggest 2-3 specific actionable steps the user can take to save money or lower their risk score.
"""
    print("\nExact System Prompt Sent to LLM:")
    print("-" * 60)
    print(system_prompt_generated)
    print("-" * 60)

    # Execute full AIService.chat call
    print("\nExecuting AIService.chat() for question: 'how many payments do I have this week?'...")
    ai_result = AIService.chat(test_user_id, "how many payments do I have this week?")
    print("\nRaw Return Payload from AIService.chat():")
    print(json.dumps(ai_result, indent=2))

    print("\n=" * 80)
    print("END OF DIAGNOSTIC AUDIT")
    print("=" * 80)


if __name__ == "__main__":
    run_diagnostics()
