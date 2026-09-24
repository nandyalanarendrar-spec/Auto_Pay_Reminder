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
# 🤖 MULTI-AGENT ORCHESTRATION ENGINE WITH LIVE DATABASE INGESTION
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
            lines = [f"📅 **Live Autopay & Revoke Schedule for All Subscriptions ({len(subs)} Total)**:\n"]
            sorted_subs = sorted(subs, key=lambda x: str(x.get("next_payment_date") or ""))
            for s in sorted_subs:
                name = s.get("merchant_name") or s.get("name")
                p_date = s.get("next_payment_date") or s.get("next_renewal_date") or "N/A"
                amt = float(s.get("amount") or 0.0)
                st = " (Free Trial)" if (s.get("is_free_trial") or s.get("status") == "trial") else ""
                try:
                    r_date = str(datetime.strptime(p_date[:10], "%Y-%m-%d").date() - timedelta(days=1))
                except Exception:
                    r_date = "N/A"
                lines.append(f"• **{name}**{st}: Autopay on **{p_date}** (Safe Revoke Deadline: **{r_date}**) — ₹{amt:,.2f}")
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
            amt = float(e.get("installment_amount") or e.get("monthly_installment") or 0.0)
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

        keywords = ["how many", "count", "total subscriptions", "present", "active", "subscriptions", "my subscriptions", "list", "show me", "tell me"]
        if any(w in msg_lower for w in keywords):
            subs_list = []
            for i, s in enumerate(subs):
                name = s.get('merchant_name') or s.get('name')
                amt = float(s.get('amount', 0))
                date_val = s.get('next_payment_date') or s.get('next_renewal_date') or 'N/A'
                st = " (Free Trial)" if (s.get("is_free_trial") or s.get("status") == "trial") else ""
                subs_list.append(f"{i+1}. **{name}**{st}: ₹{amt:,.2f}/mo (Autopay Date: {date_val})")

            subs_str = "\n".join(subs_list) if subs_list else "No active subscriptions found."
            return (
                f"You currently have **{len(subs)} active subscriptions** (including free trials). Here is the complete live breakdown from your database:\n\n"
                f"{subs_str}\n\n"
                f"**Total Monthly Subscriptions Outflow:** ₹{monthly_subs:,.2f}\n\n"
                f"--- \n"
                f"### 💡 Actionable Insights:\n"
                f"1. **Consolidate AI & Software Subscriptions**: Review redundant tools to save up to ₹3,398/mo.\n"
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
        Fetches live ground truth data from Supabase PostgreSQL (both active and free trial items)
        and routes queries to specialized agents or Gemini LLM.
        """
        clean_uid = str(user_id).strip('"\'')

        # 1. Fetch ALL Live Ground Truth Subscriptions (active + trial)
        try:
            raw_subs = SubscriptionService.get_user_subscriptions(clean_uid)
            # Include all non-cancelled subscriptions
            subs = [s for s in raw_subs if s.get("status") != "cancelled"]
        except Exception as e:
            print("Error fetching user subscriptions for AI Service:", e)
            subs = []

        try:
            raw_emis = EMIService.get_user_emis(clean_uid)
            emis = [e for e in raw_emis if e.get("status") != "cancelled"]
        except Exception as e:
            print("Error fetching user EMIs for AI Service:", e)
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
            subs_lines = []
            for s in subs:
                name = s.get('merchant_name') or s.get('name') or "Subscription"
                amt = float(s.get('amount', 0))
                freq = s.get('billing_frequency') or s.get('billing_cycle') or 'monthly'
                p_date = s.get('next_payment_date') or s.get('next_renewal_date') or 'N/A'
                st = "Free Trial" if (s.get("is_free_trial") or s.get("status") == "trial") else "Active"
                subs_lines.append(f"- {name}: ₹{amt:,.2f}/{freq} (Status: {st}, Autopay Date: {p_date})")
            
            subs_text = "\n".join(subs_lines) if subs_lines else "None"

            emis_lines = []
            for e in emis:
                name = e.get('loan_name') or e.get('merchant_name') or "EMI Loan"
                amt = float(e.get('installment_amount') or e.get('monthly_installment', 0))
                due = e.get('next_due_date') or 'N/A'
                emis_lines.append(f"- {name}: ₹{amt:,.2f}/mo (Next Due Date: {due})")
            
            emis_text = "\n".join(emis_lines) if emis_lines else "None"

            system_prompt = f"""
You are Autopay Guard AI, a smart personal financial assistant in India.
Your answers MUST be 100% genuine, factual, and strictly based on the user's real live database records below.

LIVE USER DATABASE RECORDS (Amounts in INR - ₹):
Active Subscriptions & Free Trials ({len(subs)} Total):
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
1. If the user asks to list or show their active subscriptions or ask how many exist, list EVERY SINGLE subscription from the records above ({len(subs)} Total) including all free trials (e.g., freefire, ChatGPT Plus, gym, my_jio, Adobe, Notion AI, Netflix, claude).
2. Compute and state the exact total sum (₹{monthly_subs:,.2f}/month).
3. If the user asks for the date or last date of ANY subscription, state the exact Autopay Date from the records and calculate the Safe Revoke Date (1 day prior to Autopay Date).
4. NEVER omit any item from the user's live database list.
"""
            candidate_models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-3.6-flash", "gemini-pro", "gemini-flash-latest"]
            payload_data = {"contents": [{"parts": [{"text": system_prompt}]}]}
            req_bytes = json.dumps(payload_data).encode("utf-8")

            for model in candidate_models:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
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
                except Exception as model_err:
                    print(f"Gemini API model {model} attempt note:", model_err)

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
