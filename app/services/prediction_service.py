from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid

from app.services.subscription_service import SubscriptionService
from app.services.emi_service import EMIService

def evaluate_urgency(days_left: int) -> tuple:
    """
    Evaluates payment urgency level and emoji icon based on days left until debit.
    """
    if days_left > 7:
        return ("normal", "🟢")
    elif 4 <= days_left <= 7:
        return ("upcoming", "🟡")
    elif 2 <= days_left <= 3:
        return ("prepare", "🟠")
    elif days_left == 1:
        return ("tomorrow", "🔴")
    elif days_left == 0:
        return ("due_today", "🚨")
    else:
        return ("overdue", "⚠️")

def auto_advance_date(target_date: date, frequency: str = "monthly") -> date:
    """
    Auto-advances passed payment dates to the next future billing cycle using calendar-aware month arithmetic.
    """
    from app.services.subscription_service import SubscriptionService
    rolled_str = SubscriptionService.calculate_rolled_over_date(str(target_date), frequency)
    try:
        return datetime.strptime(rolled_str[:10], "%Y-%m-%d").date()
    except Exception:
        return target_date

def parse_date(date_val: Any) -> date:
    if isinstance(date_val, str):
        return datetime.strptime(date_val[:10], "%Y-%m-%d").date()
    elif isinstance(date_val, datetime):
        return date_val.date()
    elif isinstance(date_val, date):
        return date_val
    return date.today()

class PredictionService:

    @staticmethod
    def get_subscription_countdown(user_id: str, subscription_id: str) -> Optional[Dict[str, Any]]:
        sub = SubscriptionService.get_subscription_by_id(user_id, subscription_id)
        if not sub:
            return None

        today = date.today()
        raw_date = parse_date(sub.get("next_payment_date") or sub.get("next_renewal_date") or today)
        freq = sub.get("billing_frequency") or sub.get("billing_cycle") or "monthly"
        
        # Auto advance passed date
        next_date = auto_advance_date(raw_date, freq)
        days_left = (next_date - today).days
        urgency_level, urgency_icon = evaluate_urgency(days_left)

        return {
            "subscription_id": sub.get("id"),
            "merchant_name": sub.get("merchant_name") or sub.get("name"),
            "expected_amount": float(sub.get("amount", 0)),
            "billing_frequency": freq,
            "expected_date": next_date,
            "days_left": days_left,
            "urgency_level": urgency_level,
            "urgency_icon": urgency_icon,
            "autopay_enabled": bool(sub.get("autopay_enabled", True))
        }

    @staticmethod
    def get_upcoming_payments(user_id: str) -> Dict[str, Any]:
        today = date.today()
        upcoming_items = []

        # 1. Fetch Subscriptions
        user_subs = SubscriptionService.get_user_subscriptions(user_id)
        for s in user_subs:
            if s.get("status") in ["cancelled", "inactive"]:
                continue

            merchant = s.get("merchant_name") or s.get("name", "Subscription")
            category = s.get("category", "General")
            amount = float(s.get("amount", 0))
            freq = s.get("billing_frequency") or s.get("billing_cycle") or "monthly"
            raw_date = parse_date(s.get("next_payment_date") or s.get("next_renewal_date") or today)
            
            next_date = auto_advance_date(raw_date, freq)
            days_left = (next_date - today).days
            urgency_level, urgency_icon = evaluate_urgency(days_left)

            upcoming_items.append({
                "item_type": "subscription",
                "id": str(s.get("id")),
                "name": merchant,
                "category": category,
                "amount": amount,
                "frequency_or_loan": freq,
                "next_date": next_date,
                "days_left": days_left,
                "urgency_level": urgency_level,
                "urgency_icon": urgency_icon,
                "autopay_enabled": bool(s.get("autopay_enabled", True)),
                "status": s.get("status", "active")
            })

        # 2. Fetch EMIs
        user_emis = EMIService.get_user_emis(user_id)
        for e in user_emis:
            if e.get("status") in ["completed", "cancelled"]:
                continue

            loan_name = e.get("loan_name", "EMI Loan")
            amount = float(e.get("installment_amount", 0))
            paid = e.get("installments_paid", 0)
            total = e.get("total_installments", 1)
            raw_date = parse_date(e.get("next_due_date") or today)

            next_date = auto_advance_date(raw_date, "monthly")
            days_left = (next_date - today).days
            urgency_level, urgency_icon = evaluate_urgency(days_left)

            upcoming_items.append({
                "item_type": "emi",
                "id": str(e.get("id")),
                "name": loan_name,
                "category": "EMI / Loan",
                "amount": amount,
                "frequency_or_loan": f"EMI ({paid}/{total})",
                "next_date": next_date,
                "days_left": days_left,
                "urgency_level": urgency_level,
                "urgency_icon": urgency_icon,
                "autopay_enabled": True,
                "status": e.get("status", "active")
            })

        # Sort by days_left ascending
        upcoming_items.sort(key=lambda x: x["days_left"])

        return {
            "message": f"Retrieved {len(upcoming_items)} upcoming payments for dashboard.",
            "user_id": uuid.UUID(user_id) if isinstance(user_id, str) and len(user_id) == 36 else user_id,
            "total_count": len(upcoming_items),
            "upcoming_payments": upcoming_items
        }

    @staticmethod
    def get_financial_forecast(user_id: str, days: int = 30) -> Dict[str, Any]:
        all_upcoming = PredictionService.get_upcoming_payments(user_id)["upcoming_payments"]
        
        # Filter items due within the N days forecast window (including overdue or due today)
        forecast_items = [item for item in all_upcoming if item["days_left"] <= days]

        sub_total = sum(item["amount"] for item in forecast_items if item["item_type"] == "subscription")
        emi_total = sum(item["amount"] for item in forecast_items if item["item_type"] == "emi")
        total_amount = round(sub_total + emi_total, 2)

        return {
            "message": f"{days}-Day Financial Cashflow Forecast computed successfully.",
            "user_id": uuid.UUID(user_id) if isinstance(user_id, str) and len(user_id) == 36 else user_id,
            "forecast_days": days,
            "total_forecast_amount": total_amount,
            "subscription_total": round(sub_total, 2),
            "emi_total": round(emi_total, 2),
            "item_count": len(forecast_items),
            "items": forecast_items
        }
