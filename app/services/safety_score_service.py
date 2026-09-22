from typing import List, Dict, Any
from datetime import date, datetime
import uuid

from app.services.anomaly_detector_service import AnomalyDetectorService
from app.services.prediction_service import PredictionService
from app.services.subscription_service import SubscriptionService

class SafetyScoreService:

    @staticmethod
    def get_user_safety_score(user_id: Any) -> Dict[str, Any]:
        """
        Calculates a composite Financial Safety Risk Score (0-100) for the user.
        Base score = 100 with weighted risk deductions and detailed factor breakdown.
        """
        str_user_id = str(user_id)
        contributing_factors = []
        base_score = 100

        # 1. Fetch Anomalies (Price hikes, unknown merchants, duplicates)
        anom_data = AnomalyDetectorService.detect_anomalies(str_user_id)
        for a in anom_data.get("anomalies", []):
            a_type = a.get("anomaly_type")
            if a_type == "price_increase":
                contributing_factors.append({
                    "factor_name": "Active Price Hike",
                    "impact_points": -15,
                    "severity": "high",
                    "description": a.get("description", "Price increase detected on subscription.")
                })
            elif a_type == "unknown_merchant":
                contributing_factors.append({
                    "factor_name": "Unrecognized Merchant Debit",
                    "impact_points": -20,
                    "severity": "high",
                    "description": a.get("description", "Unrecognized merchant transaction detected.")
                })
            elif a_type == "possible_duplicate":
                contributing_factors.append({
                    "factor_name": "Duplicate Subscriptions in Category",
                    "impact_points": -10,
                    "severity": "low",
                    "description": a.get("description", "Multiple active subscriptions found in same category.")
                })

        # 2. Fetch Free Trial Conversions Nearing Expiry (<= 3 days)
        today = date.today()
        user_subs = SubscriptionService.get_user_subscriptions(str_user_id)
        for s in user_subs:
            is_trial = s.get("is_free_trial") or s.get("status") == "trial"
            if is_trial and s.get("status") != "cancelled":
                raw_d = s.get("next_payment_date") or s.get("next_renewal_date") or s.get("trial_end_date")
                if raw_d:
                    if isinstance(raw_d, str):
                        t_date = datetime.strptime(raw_d[:10], "%Y-%m-%d").date()
                    elif isinstance(raw_d, (date, datetime)):
                        t_date = raw_d if isinstance(raw_d, date) else raw_d.date()
                    else:
                        t_date = today

                    days_left = (t_date - today).days
                    if 0 <= days_left <= 3:
                        name = s.get("merchant_name") or s.get("name", "Trial Service")
                        amt = float(s.get("amount", 0))
                        contributing_factors.append({
                            "factor_name": "Free Trial Auto-Conversion Trap",
                            "impact_points": -25,
                            "severity": "high",
                            "description": f"Free trial '{name}' converts to paid auto-debit of ₹{amt:.2f} in {days_left} day(s)."
                        })

        # 3. Fetch Upcoming Large Payments (> ₹3,000 in <= 3 days)
        upcoming_data = PredictionService.get_upcoming_payments(str_user_id)
        for item in upcoming_data.get("upcoming_payments", []):
            if item.get("amount", 0) >= 3000 and 0 <= item.get("days_left", 99) <= 3:
                contributing_factors.append({
                    "factor_name": "Imminent Large Debit",
                    "impact_points": -15,
                    "severity": "medium",
                    "description": f"Large upcoming debit of ₹{item['amount']:.2f} for '{item['name']}' due in {item['days_left']} day(s)."
                })

        # Calculate final composite score
        total_deductions = sum(abs(f["impact_points"]) for f in contributing_factors)
        final_score = max(0, min(100, base_score - total_deductions))

        # Determine health grade & summary
        if final_score >= 80:
            grade = "EXCELLENT"
            icon = "🟢"
            summary = "Your subscription finances are highly secure and optimized."
        elif 60 <= final_score < 80:
            grade = "GOOD"
            icon = "🟡"
            summary = "Financial health is stable with minor optimization warnings."
        elif 40 <= final_score < 60:
            grade = "MODERATE_RISK"
            icon = "🟠"
            summary = "Moderate financial risk detected. Review trial traps and price hikes."
        else:
            grade = "HIGH_RISK"
            icon = "🔴"
            summary = "High financial risk! Immediate review of active debits required."

        return {
            "message": "Calculated composite Financial Safety Risk Score successfully.",
            "user_id": uuid.UUID(str_user_id) if len(str_user_id) == 36 else str_user_id,
            "safety_score": final_score,
            "status_grade": grade,
            "status_icon": icon,
            "summary": summary,
            "deductions_total": total_deductions,
            "contributing_factors": contributing_factors
        }
