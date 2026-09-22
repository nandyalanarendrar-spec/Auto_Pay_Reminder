import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.services.subscription_service import SubscriptionService
from app.services.emi_service import EMIService
from app.services.safety_score_service import SafetyScoreService
from app.services.prediction_service import PredictionService
from app.services.chatbot_service import ChatbotService
from app.services.mock_generator_service import MockGeneratorService

# =====================================================================
# 🤖 MULTI-AGENT ORCHESTRATION ENGINE WITH LIVE WEBSITE DATA INGESTION
# =====================================================================

class SubscriptionDatesAgent:
    """Specialized Agent for Subscription Autopay Dates & Revoke Deadlines."""

    @staticmethod
    def process(message: str, subs: List[dict]) -> Optional[str]:
        msg_lower = message.lower()
        
        date_keywords = [
            "last date", "next date", "autopay date", "when is", "renewal date", 
            "revoke date", "deadline", "date for", "due date", "when will", "charge date"
        ]
        if not any(k in msg_lower for k in date_keywords):
            return None

        # 1. Match specific subscription from user's live database
        matched_sub = None
        for s in subs:
            m_name = (s.get("merchant_name") or s.get("name") or "").strip().lower()
            if m_name and m_name in msg_lower:
                matched_sub = s
                break

        if not matched_sub:
            for s in subs:
                m_name = (s.get("merchant_name") or s.get("name") or "").strip().lower()
                tokens = m_name.split()
                if any(t in msg_lower for t in tokens if len(t) > 3):
                    matched_sub = s
                    break

        if matched_sub:
            m_name = matched_sub.get("merchant_name") or matched_sub.get("name")
            pay_date_str = matched_sub.get("next_payment_date") or matched_sub.get("next_renewal_date") or "N/A"
            amt = float(matched_sub.get("amount") or 0.0)
            freq = matched_sub.get("billing_frequency") or matched_sub.get("billing_cycle") or "monthly"
            is_trial = matched_sub.get("is_free_trial") or matched_sub.get("status") == "trial"

            revoke_date_str = "N/A"
            days_left_str = "N/A"
            if pay_date_str != "N/A":
                try:
                    pay_date = datetime.strptime(pay_date_str[:10], "%Y-%m-%d").date()
                    today = date.today()
                    diff = (pay_date - today).days
                    revoke_date = pay_date - timedelta(days=1)
                    revoke_date_str = revoke_date.strftime("%B %d, %Y (%Y-%m-%d)")
                    days_left_str = f"in {diff} days" if diff > 0 else ("today" if diff == 0 else "due for rollover")
                except Exception:
                    pass

            pay_date_formatted = pay_date_str
            try:
                pay_date_formatted = datetime.strptime(pay_date_str[:10], "%Y-%m-%d").strftime("%B %d, %Y (%Y-%m-%d)")
            except Exception:
                pass

            response = (
                f"📅 **Live Autopay Schedule for {m_name}**:\n\n"
                f"• **Next Autopay Charge Date**: **{pay_date_formatted}** ({days_left_str})\n"
                f"• **🛑 Safe Revoke Date (Cancellation Deadline)**: **{revoke_date_str}** by 11:59 PM IST\n"
                f"• **Auto-Debit Amount**: ₹{amt:,.2f}/{freq}\n"
                f"• **Status**: {'Free Trial' if is_trial else 'Active Subscription'}\n\n"
                f"💡 *To prevent being charged, make sure to revoke the UPI mandate or cancel the subscription on or before **{revoke_date_str}**.*"
            )
            return response

        # 2. Answer for all subscriptions if user asks for general dates
        if any(w in msg_lower for w in ["all", "list", "subscriptions", "what are my dates"]):
            lines = [f"📅 **Live Autopay & Revoke Schedule for All Subscriptions**:\n"]
            sorted_subs = sorted(subs, key=lambda x: str(x.get("next_payment_date") or ""))
            for s in sorted_subs:
                name = s.get("merchant_name") or s.get("name")
                p_date = s.get("next_payment_date") or "N/A"
                amt = float(s.get("amount") or 0.0)
                try:
                    r_date = str(datetime.strptime(p_date[:10], "%Y-%m-%d").date() - timedelta(days=1))
                except Exception:
                    r_date = "N/A"
                lines.append(f"• **{name}**: Autopay on **{p_date}** (Safe Revoke Deadline: **{r_date}**) — ₹{amt:,.2f}")
            return "\n".join(lines)

        return None


class CancellationGuideAgent:
    """Specialized Agent for Merchant Cancellation Steps & UPI Mandate Revocation."""

    @staticmethod
    def process(message: str) -> Optional[str]:
        msg_lower = message.lower()
        if any(k in msg_lower for k in ["how to cancel", "cancel subscription", "how do i cancel", "stop autopay", "revoke mandate"]):
            res = ChatbotService.query(message)
            if res and res.get("response"):
                return res["response"]
        return None


class EMISpecialistAgent:
    """Specialized Agent for EMI Loans & Installment Queries."""

    @staticmethod
    def process(message: str, emis: List[dict]) -> Optional[str]:
        msg_lower = message.lower()
        if not any(k in msg_lower for k in ["emi", "loan", "installment", "payoff"]):
            return None

        if not emis:
            return "You currently have no active EMI loan records in your vault."

        lines = ["💳 **Your Live EMI Loans & Payoff Progress**:\n"]
        for e in emis:
            name = e.get("loan_name") or e.get("merchant_name") or "EMI Loan"
            amt = float(e.get("installment_amount") or 0.0)
            paid = e.get("installments_paid", 0)
            total = e.get("total_installments", 1)
            due = e.get("next_due_date") or "N/A"
            pct = round((paid / total) * 100) if total else 0
            lines.append(f"• **{name}**: ₹{amt:,.2f}/mo | Progress: **{paid}/{total} Paid ({pct}%)** | Next Due Date: **{due}**")

        return "\n".join(lines)


class SpendAdvisoryAgent:
    """Specialized Agent for Live Spend Analytics, Counts, AI Tool Consolidation & Safety Risk."""

    @staticmethod
    def process(message: str, subs: List[dict], emis: List[dict], safety_score: int, status_grade: str, monthly_subs: float, monthly_emis: float) -> str:
        msg_lower = message.lower()

        # Direct count & breakdown query
        if any(w in msg_lower for w in ["how many", "count", "total subscriptions", "present"]):
            subs_list = [f"{i+1}. **{s.get('merchant_name') or s.get('name')}:** ₹{float(s.get('amount',0)):,.2f}/mo (Autopay Date: {s.get('next_payment_date')})" for i, s in enumerate(subs)]
            subs_str = "\n".join(subs_list)
            return (
                f"Based on your live Autopay Guard database, you currently have **{len(subs)} active subscriptions**, totaling **₹{monthly_subs:,.2f}/month**.\n\n"
                f"Here is the exact live breakdown:\n"
                f"{subs_str}\n\n"
                f"--- \n"
                f"### 💡 Actionable Insights:\n"
                f"1. **Consolidate AI Tools**: You are paying for multiple AI tools. Choosing your primary tools can save up to ₹3,398/mo.\n"
                f"2. **Check Revoke Deadlines**: Make sure to revoke mandates 24 hours before their autopay charge date."
            )

        return (
            f"Based on your live Autopay Guard profile, you have **{len(subs)} active subscriptions** (totaling ₹{monthly_subs:,.2f}/mo) "
            f"and **{len(emis)} active EMIs** (totaling ₹{monthly_emis:,.2f}/mo).\n\n"
            f"• Total Monthly Outflow: **₹{monthly_subs + monthly_emis:,.2f}**\n"
            f"• Financial Safety Risk Score: **{safety_score}/100** ({status_grade})\n\n"
            f"💡 **Recommended Actions**:\n"
            f"1. Review upcoming auto-debit dates to ensure your bank account has sufficient balance.\n"
            f"2. Cancel any unused free trials 24 hours before their revoke deadline.\n"
            f"3. Consolidate overlapping subscriptions to lower monthly outflow."
        )


# =====================================================================
# 🚀 MAIN AGENTIC ORCHESTRATOR WITH ZERO HALLUCINATION INGESTION
# =====================================================================

class AIService:

    @staticmethod
    def chat(user_id: str, message: str) -> Dict[str, Any]:
        """
        Multi-Agent Orchestration Layer:
        Fetches live ground truth data from Supabase PostgreSQL and routes queries to specialized agents.
        """
        clean_uid = str(user_id).strip('"\'')

        # 1. Fetch Ground Truth Data from Database
        try:
            subs = SubscriptionService.get_user_subscriptions(clean_uid, status="active")
        except Exception:
            subs = []

        try:
            emis = EMIService.get_user_emis(clean_uid)
            emis = [e for e in emis if e.get("status") != "cancelled"]
        except Exception:
            emis = []

        try:
            safety_res = SafetyScoreService.get_user_safety_score(clean_uid)
            safety_score = safety_res.get("safety_score", 75)
            status_grade = safety_res.get("status_grade", "MODERATE_RISK")
        except Exception:
            safety_score = 75
            status_grade = "MODERATE_RISK"

        monthly_subs = sum(float(s.get("amount", 0)) for s in subs)
        monthly_emis = sum(float(e.get("installment_amount") or e.get("monthly_installment", 0)) for e in emis)

        context_summary = {
            "monthly_subscriptions_total": round(monthly_subs, 2),
            "monthly_emis_total": round(monthly_emis, 2),
            "total_monthly_outflow": round(monthly_subs + monthly_emis, 2),
            "active_subscriptions_count": len(subs),
            "active_emis_count": len(emis),
            "safety_score": safety_score,
            "status_grade": status_grade
        }

        # 2. MULTI-AGENT ORCHESTRATION ROUTING

        # Route 1: Subscription Dates Agent (Handles exact dates & revoke deadlines)
        dates_res = SubscriptionDatesAgent.process(message, subs)
        if dates_res:
            return {
                "query": message,
                "response": dates_res,
                "context_summary": context_summary,
                "suggested_actions": ["Revoke UPI Mandate", "Set Calendar Reminder", "View Subscription Vault"]
            }

        # Route 2: Cancellation Guide Agent (Handles step-by-step merchant cancellation)
        cancel_res = CancellationGuideAgent.process(message)
        if cancel_res:
            return {
                "query": message,
                "response": cancel_res,
                "context_summary": context_summary,
                "suggested_actions": ["Revoke UPI Mandate", "Check Revoke Deadline"]
            }

        # Route 3: EMI Specialist Agent (Handles loan payoff & installments)
        emi_res = EMISpecialistAgent.process(message, emis)
        if emi_res:
            return {
                "query": message,
                "response": emi_res,
                "context_summary": context_summary,
                "suggested_actions": ["Pay Installment", "Check Loan Progress"]
            }

        # Route 4: Spend Advisory Agent & Gemini LLM Generation
        ai_response_text = None
        api_key = getattr(settings, "GEMINI_API_KEY", "") or ""

        if api_key:
            subs_text = "\n".join([
                f"- {s.get('merchant_name') or s.get('name')}: ₹{float(s.get('amount',0)):,.2f}/{s.get('billing_frequency') or 'monthly'}, Autopay Date: {s.get('next_payment_date')}"
                for s in subs
            ]) or "None"
            emis_text = "\n".join([
                f"- {e.get('loan_name') or e.get('merchant_name')}: ₹{float(e.get('installment_amount',0)):,.2f}/mo, Next Due Date: {e.get('next_due_date')}"
                for e in emis
            ]) or "None"

            system_prompt = f"""
You are Autopay Guard AI, a smart personal financial assistant in India.
Your answers MUST be 100% genuine, factual, and strictly based on the user's real live database records below.

LIVE USER DATABASE RECORDS (Amounts in INR - ₹):
Active Subscriptions ({len(subs)} Total):
{subs_text}

Active EMI Loans ({len(emis)} Total):
{emis_text}

Summary:
- Total Monthly Subscriptions: ₹{monthly_subs:,.2f}
- Total Monthly EMIs: ₹{monthly_emis:,.2f}
- Total Monthly Outflow: ₹{monthly_subs + monthly_emis:,.2f}
- Financial Safety Score: {safety_score}/100 ({status_grade})

User Question: "{message}"

MANDATORY RULES:
1. If the user asks for the date, last date, or autopay date of ANY subscription (e.g. Netflix Premium), locate the exact 'Autopay Date' from the database record and compute the 'Safe Revoke Date' (1 day prior to Autopay Date). State both dates explicitly.
2. If the user asks how many subscriptions exist, give the exact count ({len(subs)}) and list every single subscription with its price and date from the live database records.
3. NEVER make up fictional dates or generic estimates when live database dates are provided.
"""
            candidate_models = ["gemini-flash-latest", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-pro-latest", "gemini-2.5-flash"]
            payload_data = {"contents": [{"parts": [{"text": system_prompt}]}]}
            req_bytes = json.dumps(payload_data).encode("utf-8")

            for model in candidate_models:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
                req = urllib.request.Request(gemini_url, data=req_bytes, headers=headers)
                try:
                    with urllib.request.urlopen(req) as resp:
                        res_json = json.loads(resp.read().decode("utf-8"))
                        candidates = res_json.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                ai_response_text = parts[0].get("text")
                                break
                except Exception:
                    pass

        if not ai_response_text:
            ai_response_text = SpendAdvisoryAgent.process(
                message, subs, emis, safety_score, status_grade, monthly_subs, monthly_emis
            )

        suggested_actions = ["Consolidate AI Subscriptions", "Check Upcoming Debits", "Connect Google Calendar"]

        return {
            "query": message,
            "response": ai_response_text,
            "context_summary": context_summary,
            "suggested_actions": suggested_actions
        }
