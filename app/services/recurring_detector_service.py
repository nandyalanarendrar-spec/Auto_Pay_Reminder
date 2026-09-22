import numpy as np
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List, Dict, Any, Optional
import uuid

from app.core.security import get_supabase_client
from app.services.mock_generator_service import MockGeneratorService
from app.services.subscription_service import SubscriptionService
from app.schemas.subscription import SubscriptionCreate

# Helper to infer category based on merchant name keywords
def infer_merchant_category(merchant_name: str) -> str:
    name = merchant_name.lower()
    if any(k in name for k in ["netflix", "spotify", "prime", "hotstar", "youtube"]):
        return "Entertainment"
    elif any(k in name for k in ["aws", "chatgpt", "openai", "github", "google", "icloud", "adobe"]):
        return "Software & AI"
    elif any(k in name for k in ["gym", "cult", "fitness"]):
        return "Gym & Fitness"
    elif any(k in name for k in ["jio", "airtel", "vi", "bescom", "electricity", "broadband", "act"]):
        return "Utilities"
    elif any(k in name for k in ["swiggy", "zomato"]):
        return "Food & Dining"
    return "General"

class RecurringDetectorService:
    @staticmethod
    def detect_recurring_payments(
        db: Any,
        user_id: Any,
        amount_tolerance_pct: float = 0.10,
        monthly_date_tolerance_days: int = 3,
        yearly_date_tolerance_days: int = 10,
        auto_create_subscriptions: bool = True
    ) -> Dict[str, Any]:
        """
        Rule-based algorithm to discover recurring payment patterns from raw user transactions.
        Operates via Supabase REST API & memory store fallback for maximum resilience.
        """
        str_user_id = str(user_id)
        
        # Fetch user transactions via Supabase REST API / Memory Fallback
        all_transactions = MockGeneratorService.get_user_transactions(str_user_id)

        if not all_transactions:
            return {
                "message": "No transactions found for the user. Please generate mock transactions first.",
                "user_id": str_user_id,
                "detected_count": 0,
                "updated_transactions_count": 0,
                "detected_subscriptions": []
            }

        # Group transactions by normalized merchant name
        merchant_groups: Dict[str, List[dict]] = {}
        for tx in all_transactions:
            m_key = tx.get("merchant_name", "").strip()
            if m_key:
                merchant_groups.setdefault(m_key, []).append(tx)

        detected_subscriptions = []
        updated_tx_ids = []

        for merchant_name, txs in merchant_groups.items():
            # Condition 1: Must have 3+ transactions
            if len(txs) < 3:
                continue

            # Parse transaction dates and sort ascending
            parsed_txs = []
            for tx in txs:
                d_val = tx.get("transaction_date")
                if isinstance(d_val, str):
                    d_obj = datetime.strptime(d_val[:10], "%Y-%m-%d").date()
                elif isinstance(d_val, (date, datetime)):
                    d_obj = d_val if isinstance(d_val, date) else d_val.date()
                else:
                    continue
                parsed_txs.append((d_obj, tx))

            if len(parsed_txs) < 3:
                continue

            parsed_txs.sort(key=lambda x: x[0])
            dates = [p[0] for p in parsed_txs]
            tx_objs = [p[1] for p in parsed_txs]

            amounts = [float(tx.get("amount", 0)) for tx in tx_objs]
            mean_amount = sum(amounts) / len(amounts)
            if mean_amount <= 0:
                continue

            # Amount consistency check
            max_dev = max(abs(amt - mean_amount) for amt in amounts) / mean_amount
            if max_dev > amount_tolerance_pct:
                continue

            amount_std = np.std(amounts) if len(amounts) > 1 else 0.0
            amount_score = max(0.0, 1.0 - (amount_std / mean_amount))

            # Date interval consistency check
            gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates) - 1)]
            avg_gap = sum(gaps) / len(gaps)

            billing_frequency = None
            date_tolerance = 3
            expected_cycle_gap = 30

            if 25 <= avg_gap <= 35:
                billing_frequency = "monthly"
                expected_cycle_gap = 30
                date_tolerance = monthly_date_tolerance_days
            elif 350 <= avg_gap <= 380:
                billing_frequency = "yearly"
                expected_cycle_gap = 365
                date_tolerance = yearly_date_tolerance_days
            elif 5 <= avg_gap <= 9:
                billing_frequency = "weekly"
                expected_cycle_gap = 7
                date_tolerance = 2

            if not billing_frequency:
                continue

            # Check if all gap deviations are within tolerance
            gap_deviations = [abs(g - expected_cycle_gap) for g in gaps]
            if any(dev > date_tolerance for dev in gap_deviations):
                continue

            gap_std = np.std(gaps) if len(gaps) > 1 else 0.0
            date_score = max(0.0, 1.0 - (gap_std / max(1.0, float(date_tolerance))))

            # Confidence score calculation (0 - 100%)
            confidence_score = int(round((0.5 * amount_score + 0.5 * date_score) * 100))
            confidence_score = max(50, min(100, confidence_score))

            # Collect matching transaction IDs to update is_labeled_recurring
            for tx in tx_objs:
                if not tx.get("is_labeled_recurring"):
                    tx["is_labeled_recurring"] = True
                    if tx.get("id"):
                        updated_tx_ids.append(tx["id"])

            # Determine next payment date using calendar-aware rollover calculation
            last_date = dates[-1]
            from app.services.subscription_service import SubscriptionService
            rolled_str = SubscriptionService.calculate_rolled_over_date(str(last_date), billing_frequency)
            try:
                next_payment_date = datetime.strptime(rolled_str[:10], "%Y-%m-%d").date()
            except Exception:
                next_payment_date = last_date

            category = infer_merchant_category(merchant_name)
            sub_id = None
            status = "pending_confirmation"

            # Check existing user subscriptions
            user_subs = SubscriptionService.get_user_subscriptions(str_user_id)
            existing = next((s for s in user_subs if s.get("merchant_name", "").lower() == merchant_name.lower()), None)

            if existing:
                sub_id = existing.get("id")
                status = existing.get("status", "active")
            elif auto_create_subscriptions:
                sub_create_payload = SubscriptionCreate(
                    merchant_name=merchant_name,
                    category=category,
                    amount=round(mean_amount, 2),
                    billing_frequency=billing_frequency,
                    start_date=dates[0],
                    next_payment_date=next_payment_date,
                    status="pending_confirmation",
                    is_recurring=True,
                    autopay_enabled=True,
                    risk_score=10,
                    source="detected"
                )
                created_sub = SubscriptionService.create_subscription(db=None, user_id=str_user_id, payload=sub_create_payload)
                sub_id = created_sub.get("id")
                status = "pending_confirmation"

            detected_subscriptions.append({
                "subscription_id": sub_id,
                "merchant_name": merchant_name,
                "category": category,
                "expected_amount": round(mean_amount, 2),
                "billing_frequency": billing_frequency,
                "confidence_score": confidence_score,
                "first_transaction_date": dates[0],
                "last_transaction_date": dates[-1],
                "next_payment_date": next_payment_date,
                "matching_transactions_count": len(parsed_txs),
                "status": status
            })

        # Update labeled transactions via Supabase REST Client
        if updated_tx_ids:
            try:
                supabase = get_supabase_client()
                supabase.from_("transactions").update({"is_labeled_recurring": True}).in_("id", updated_tx_ids).execute()
            except Exception as err:
                print("Supabase REST update transaction flags note:", err)

        return {
            "message": f"Successfully analyzed transactions. Detected {len(detected_subscriptions)} recurring payment patterns.",
            "user_id": str_user_id,
            "detected_count": len(detected_subscriptions),
            "updated_transactions_count": len(updated_tx_ids),
            "detected_subscriptions": detected_subscriptions
        }
