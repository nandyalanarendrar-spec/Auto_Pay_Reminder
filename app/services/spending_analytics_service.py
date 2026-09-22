from typing import List, Dict, Any, Optional
import uuid

from app.services.subscription_service import SubscriptionService
from app.services.emi_service import EMIService

class SpendingAnalyticsService:

    @staticmethod
    def get_spending_summary(user_id: Any) -> Dict[str, Any]:
        """
        Computes total normalized monthly spend, annual projected spend,
        and category-wise percentage distribution.
        """
        str_user_id = str(user_id)
        
        subs = [s for s in SubscriptionService.get_user_subscriptions(str_user_id) if s.get("status") not in ["cancelled", "inactive"]]
        emis = [e for e in EMIService.get_user_emis(str_user_id) if e.get("status") not in ["completed", "cancelled"]]

        total_monthly = 0.0
        cat_map: Dict[str, Dict[str, Any]] = {}

        # 1. Process Subscriptions
        for s in subs:
            amt = float(s.get("amount", 0))
            freq = str(s.get("billing_frequency") or s.get("billing_cycle") or "monthly").lower()
            
            if "yearly" in freq:
                monthly_amt = amt / 12.0
            elif "weekly" in freq:
                monthly_amt = amt * 4.0
            else:
                monthly_amt = amt

            total_monthly += monthly_amt
            cat = s.get("category", "General")
            
            if cat not in cat_map:
                cat_map[cat] = {"monthly_amount": 0.0, "item_count": 0}
            cat_map[cat]["monthly_amount"] += monthly_amt
            cat_map[cat]["item_count"] += 1

        # 2. Process EMIs
        for e in emis:
            inst_amt = float(e.get("installment_amount", 0))
            total_monthly += inst_amt
            cat = "EMI / Loans"
            
            if cat not in cat_map:
                cat_map[cat] = {"monthly_amount": 0.0, "item_count": 0}
            cat_map[cat]["monthly_amount"] += inst_amt
            cat_map[cat]["item_count"] += 1

        total_monthly = round(total_monthly, 2)
        total_yearly = round(total_monthly * 12.0, 2)

        # Build category breakdown items with percentage shares
        category_breakdown = []
        for cat_name, info in cat_map.items():
            m_amt = round(info["monthly_amount"], 2)
            pct = round((m_amt / total_monthly * 100.0), 2) if total_monthly > 0 else 0.0
            category_breakdown.append({
                "category": cat_name,
                "monthly_amount": m_amt,
                "percentage_of_total": pct,
                "item_count": info["item_count"]
            })

        # Sort category breakdown by monthly amount descending
        category_breakdown.sort(key=lambda x: x["monthly_amount"], reverse=True)

        return {
            "message": "Retrieved spending analytics summary successfully.",
            "user_id": uuid.UUID(str_user_id) if len(str_user_id) == 36 else str_user_id,
            "total_monthly_spend": total_monthly,
            "total_yearly_projected": total_yearly,
            "active_subscriptions_count": len(subs),
            "active_emis_count": len(emis),
            "category_breakdown": category_breakdown
        }

    @staticmethod
    def simulate_what_if_cancellation(user_id: Any, cancel_subscription_ids: List[str]) -> Dict[str, Any]:
        """
        Simulates cancelling selected subscription IDs and calculates instant monthly & annual rupee savings.
        """
        str_user_id = str(user_id)
        current_summary = SpendingAnalyticsService.get_spending_summary(str_user_id)
        current_monthly = current_summary["total_monthly_spend"]

        user_subs = SubscriptionService.get_user_subscriptions(str_user_id)
        
        cancelled_items = []
        monthly_saved = 0.0

        for s in user_subs:
            s_id = str(s.get("id"))
            m_name = s.get("merchant_name") or s.get("name", "")
            
            if s_id in cancel_subscription_ids or m_name in cancel_subscription_ids or m_name.lower() in [c.lower() for c in cancel_subscription_ids]:
                amt = float(s.get("amount", 0))
                freq = str(s.get("billing_frequency") or s.get("billing_cycle") or "monthly").lower()
                
                if "yearly" in freq:
                    m_saved = amt / 12.0
                elif "weekly" in freq:
                    m_saved = amt * 4.0
                else:
                    m_saved = amt

                monthly_saved += m_saved
                cancelled_items.append({
                    "id": s_id,
                    "merchant_name": m_name,
                    "amount": round(amt, 2),
                    "billing_frequency": freq,
                    "monthly_savings_contribution": round(m_saved, 2)
                })

        monthly_saved = round(monthly_saved, 2)
        yearly_saved = round(monthly_saved * 12.0, 2)
        after_cancel_monthly = round(max(0.0, current_monthly - monthly_saved), 2)
        pct_saved = round((monthly_saved / current_monthly * 100.0), 2) if current_monthly > 0 else 0.0

        return {
            "message": f"Simulated cancellation of {len(cancelled_items)} subscription(s).",
            "user_id": uuid.UUID(str_user_id) if len(str_user_id) == 36 else str_user_id,
            "current_monthly_total": current_monthly,
            "after_cancel_monthly_total": after_cancel_monthly,
            "monthly_savings": monthly_saved,
            "yearly_savings": yearly_saved,
            "percentage_saved": pct_saved,
            "cancelled_items": cancelled_items
        }

    @staticmethod
    def get_budget_status(user_id: Any, monthly_budget: float = 15000.0) -> Dict[str, Any]:
        """
        Compares total monthly commitments against budget cap.
        """
        str_user_id = str(user_id)
        current_summary = SpendingAnalyticsService.get_spending_summary(str_user_id)
        current_spend = current_summary["total_monthly_spend"]

        monthly_budget = round(float(monthly_budget), 2)
        is_over = current_spend > monthly_budget
        
        budget_remaining = round(max(0.0, monthly_budget - current_spend), 2)
        over_amount = round(current_spend - monthly_budget, 2) if is_over else 0.0
        utilization_pct = round((current_spend / monthly_budget * 100.0), 2) if monthly_budget > 0 else 0.0

        if is_over:
            msg = f"⚠️ Over Budget! You have exceeded your ₹{monthly_budget:,.2f} monthly budget cap by ₹{over_amount:,.2f} ({utilization_pct:.1f}% used)."
        else:
            msg = f"✅ Under Budget! You have ₹{budget_remaining:,.2f} remaining out of your ₹{monthly_budget:,.2f} monthly budget ({utilization_pct:.1f}% used)."

        return {
            "message": "Calculated budget utilization status successfully.",
            "user_id": uuid.UUID(str_user_id) if len(str_user_id) == 36 else str_user_id,
            "monthly_budget": monthly_budget,
            "current_monthly_spend": current_spend,
            "budget_remaining": budget_remaining,
            "is_over_budget": is_over,
            "over_budget_amount": over_amount,
            "budget_utilization_pct": utilization_pct,
            "status_message": msg
        }
