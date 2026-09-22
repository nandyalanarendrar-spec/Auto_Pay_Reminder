import uuid
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from app.services.mock_generator_service import MockGeneratorService
from app.services.subscription_service import SubscriptionService
from app.services.recurring_detector_service import infer_merchant_category

class AnomalyDetectorService:

    @staticmethod
    def detect_anomalies(user_id: Any, price_hike_threshold_pct: float = 0.15) -> Dict[str, Any]:
        """
        Rule-based anomaly detection engine:
        1. Price Increase Detection (latest debit > 15% above historical average)
        2. Unknown Merchant Detection (unrecognized/suspicious narration)
        3. Duplicate Category Detection (2+ active subscriptions in same category)
        """
        str_user_id = str(user_id)
        anomalies = []

        all_txns = MockGeneratorService.get_user_transactions(str_user_id)
        active_subs = [s for s in SubscriptionService.get_user_subscriptions(str_user_id) if s.get("status") not in ["cancelled", "inactive"]]

        # -------------------------------------------------------------
        # 1. Price Increase Detection
        # -------------------------------------------------------------
        merchant_groups: Dict[str, List[dict]] = {}
        for tx in all_txns:
            m_key = tx.get("merchant_name", "").strip()
            if m_key:
                merchant_groups.setdefault(m_key, []).append(tx)

        for merchant_name, txs in merchant_groups.items():
            if len(txs) < 2:
                continue

            # Price hike detection applies to recurring subscriptions only (not random noise like Swiggy/Uber)
            is_recurring_merchant = any(t.get("is_labeled_recurring") for t in txs) or \
                                    any(s.get("merchant_name", "").lower() == merchant_name.lower() for s in active_subs) or \
                                    any(k in merchant_name.lower() for k in ["netflix", "spotify", "adobe", "chatgpt", "aws", "github", "prime"])

            if not is_recurring_merchant:
                continue

            # Parse dates and sort ascending
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

            if len(parsed_txs) < 2:
                continue

            parsed_txs.sort(key=lambda x: x[0])
            latest_amt = float(parsed_txs[-1][1].get("amount", 0))
            hist_amts = [float(p[1].get("amount", 0)) for p in parsed_txs[:-1]]

            if not hist_amts:
                continue

            hist_avg = sum(hist_amts) / len(hist_amts)
            if hist_avg > 0 and latest_amt > hist_avg:
                pct_increase = ((latest_amt - hist_avg) / hist_avg) * 100.0
                if (latest_amt - hist_avg) / hist_avg >= price_hike_threshold_pct:
                    cat = infer_merchant_category(merchant_name)
                    anomalies.append({
                        "id": f"anom-hike-{uuid.uuid4().hex[:8]}",
                        "anomaly_type": "price_increase",
                        "merchant_name": merchant_name,
                        "category": cat,
                        "severity": "high",
                        "severity_icon": "🔴",
                        "description": f"Price increased by {pct_increase:.1f}% on {merchant_name} (from ₹{hist_avg:.2f} to ₹{latest_amt:.2f})",
                        "old_amount": round(hist_avg, 2),
                        "new_amount": round(latest_amt, 2),
                        "percentage_increase": round(pct_increase, 2)
                    })

        # -------------------------------------------------------------
        # 2. Unknown / Suspicious Merchant Detection
        # -------------------------------------------------------------
        seen_unknowns = set()
        for tx in all_txns:
            m_name = tx.get("merchant_name", "")
            narration = tx.get("narration", "")
            combined = f"{m_name} {narration}".upper()

            if any(k in combined for k in ["UNKNOWN", "UNRECOGNIZED", "SUSPICIOUS", "UNKNOWN_BILLING"]):
                if m_name not in seen_unknowns:
                    seen_unknowns.add(m_name)
                    amt = float(tx.get("amount", 0))
                    anomalies.append({
                        "id": f"anom-unk-{uuid.uuid4().hex[:8]}",
                        "anomaly_type": "unknown_merchant",
                        "merchant_name": m_name,
                        "category": "Uncategorized",
                        "severity": "medium",
                        "severity_icon": "🟠",
                        "description": f"Unrecognized debit of ₹{amt:.2f} from '{m_name}'",
                        "old_amount": None,
                        "new_amount": round(amt, 2),
                        "percentage_increase": None
                    })

        # -------------------------------------------------------------
        # 3. Duplicate Category Detection
        # -------------------------------------------------------------
        category_groups: Dict[str, List[dict]] = {}
        for sub in active_subs:
            cat = sub.get("category", "General")
            category_groups.setdefault(cat, []).append(sub)

        for cat, subs in category_groups.items():
            if len(subs) >= 2:
                sub_names = [s.get("merchant_name") or s.get("name", "Subscription") for s in subs]
                anomalies.append({
                    "id": f"anom-dup-{uuid.uuid4().hex[:8]}",
                    "anomaly_type": "possible_duplicate",
                    "merchant_name": ", ".join(sub_names),
                    "category": cat,
                    "severity": "low",
                    "severity_icon": "🟡",
                    "description": f"You have {len(subs)} active subscriptions in category '{cat}' ({', '.join(sub_names)}). Consider evaluating for duplicates.",
                    "old_amount": None,
                    "new_amount": None,
                    "percentage_increase": None
                })

        high_count = sum(1 for a in anomalies if a["severity"] == "high")
        med_count = sum(1 for a in anomalies if a["severity"] == "medium")
        low_count = sum(1 for a in anomalies if a["severity"] == "low")

        return {
            "message": f"Retrieved {len(anomalies)} financial anomalies.",
            "user_id": uuid.UUID(str_user_id) if len(str_user_id) == 36 else str_user_id,
            "total_anomalies": len(anomalies),
            "high_severity_count": high_count,
            "medium_severity_count": med_count,
            "low_severity_count": low_count,
            "anomalies": anomalies
        }
