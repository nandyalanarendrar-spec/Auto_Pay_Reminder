import re
import uuid
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

from app.core.security import get_supabase_client
from app.services.mock_generator_service import MockGeneratorService
from app.services.emi_service import EMIService, calculate_completion_percentage
from app.schemas.emi import EMICreate, EMIUpdate

EMI_KEYWORDS = ["EMI", "INSTALLMENT", "NACH", "ECS", "LOAN", "ACH DEBIT", "FINANCE"]

class EMIDetectorService:
    @staticmethod
    def detect_emis(user_id: Any) -> Dict[str, Any]:
        """
        Rule-based algorithm that scans transaction narration text for EMI keywords,
        extracts installment numbers, tags transactions, and auto-populates EMI records.
        """
        str_user_id = str(user_id)
        
        # Fetch user transactions via Supabase REST API / Memory Fallback
        all_transactions = MockGeneratorService.get_user_transactions(str_user_id)

        if not all_transactions:
            return {
                "message": "No transactions found for user. Generate mock transactions first.",
                "user_id": str_user_id,
                "detected_count": 0,
                "updated_transactions_count": 0,
                "detected_emis": []
            }

        # Step 1: Pre-filter transactions containing EMI keywords in narration or merchant_name
        matching_txs: List[dict] = []
        for tx in all_transactions:
            narration = str(tx.get("narration", "")).upper()
            merchant = str(tx.get("merchant_name", "")).upper()
            combined_text = f"{narration} {merchant}"

            if any(kw in combined_text for kw in EMI_KEYWORDS):
                matching_txs.append(tx)

        if not matching_txs:
            return {
                "message": "No EMI transactions found matching keywords.",
                "user_id": str_user_id,
                "detected_count": 0,
                "updated_transactions_count": 0,
                "detected_emis": []
            }

        # Step 2: Group matching transactions by merchant name
        merchant_groups: Dict[str, List[dict]] = {}
        for tx in matching_txs:
            m_key = tx.get("merchant_name", "EMI Merchant").strip()
            merchant_groups.setdefault(m_key, []).append(tx)

        detected_emis = []
        updated_tx_ids = []

        for merchant_name, group in merchant_groups.items():
            # Parse transaction dates and sort ascending
            parsed_group = []
            for tx in group:
                d_val = tx.get("transaction_date")
                if isinstance(d_val, str):
                    d_obj = datetime.strptime(d_val[:10], "%Y-%m-%d").date()
                elif isinstance(d_val, (date, datetime)):
                    d_obj = d_val if isinstance(d_val, date) else d_val.date()
                else:
                    continue
                parsed_group.append((d_obj, tx))

            if not parsed_group:
                continue

            parsed_group.sort(key=lambda x: x[0])
            dates = [p[0] for p in parsed_group]
            tx_objs = [p[1] for p in parsed_group]

            amounts = [float(tx.get("amount", 0)) for tx in tx_objs]
            installment_amount = round(sum(amounts) / len(amounts), 2)
            if installment_amount <= 0:
                continue

            # Regex check to extract "3/12" fraction pattern from narration
            extracted_paid = None
            extracted_total = None

            for tx in tx_objs:
                narration = str(tx.get("narration", ""))
                match = re.search(r"(\d{1,2})\s*/\s*(\d{1,2})", narration)
                if match:
                    extracted_paid = int(match.group(1))
                    extracted_total = int(match.group(2))

            # Calculate installment counts
            if extracted_paid is not None and extracted_total is not None:
                total_installments = max(extracted_total, len(parsed_group))
                installments_paid = max(extracted_paid, len(parsed_group))
            else:
                installments_paid = len(parsed_group)
                total_installments = max(12, installments_paid)

            last_date = dates[-1]
            next_due_date = last_date + timedelta(days=30)
            remaining_amount = round(max(0.0, (total_installments - installments_paid) * installment_amount), 2)
            completion_pct = calculate_completion_percentage(installments_paid, total_installments)
            status_val = "completed" if installments_paid >= total_installments else "active"

            # Tag transaction IDs as is_labeled_emi = True
            for tx in tx_objs:
                if not tx.get("is_labeled_emi"):
                    tx["is_labeled_emi"] = True
                    if tx.get("id"):
                        updated_tx_ids.append(tx["id"])

            # Check if EMI record already exists for user and loan_name
            user_emis = EMIService.get_user_emis(str_user_id)
            existing = next((e for e in user_emis if e.get("loan_name", "").lower() == merchant_name.lower()), None)

            emi_id = None
            if existing:
                emi_id = existing.get("id")
                # Update existing EMI record
                update_payload = EMIUpdate(
                    installments_paid=installments_paid,
                    total_installments=total_installments,
                    installment_amount=installment_amount,
                    next_due_date=next_due_date,
                    remaining_amount=remaining_amount,
                    status=status_val
                )
                updated_item = EMIService.update_emi(str_user_id, str(emi_id), update_payload)
                if updated_item:
                    status_val = updated_item.get("status", status_val)
            else:
                # Create new EMI record
                create_payload = EMICreate(
                    loan_name=merchant_name,
                    total_installments=total_installments,
                    installments_paid=installments_paid,
                    installment_amount=installment_amount,
                    start_date=dates[0],
                    next_due_date=next_due_date,
                    remaining_amount=remaining_amount,
                    status=status_val
                )
                created_item = EMIService.create_emi(str_user_id, create_payload)
                emi_id = created_item.get("id")

            detected_emis.append({
                "emi_id": emi_id,
                "loan_name": merchant_name,
                "installment_amount": installment_amount,
                "total_installments": total_installments,
                "installments_paid": installments_paid,
                "completion_percentage": completion_pct,
                "remaining_amount": remaining_amount,
                "next_due_date": next_due_date,
                "matching_transactions_count": len(parsed_group),
                "status": status_val
            })

        # Batch update is_labeled_emi = True in Supabase REST API
        if updated_tx_ids:
            try:
                supabase = get_supabase_client()
                supabase.from_("transactions").update({"is_labeled_emi": True}).in_("id", updated_tx_ids).execute()
            except Exception as err:
                print("Supabase REST update EMI transaction flags note:", err)

        return {
            "message": f"Successfully analyzed transactions. Detected {len(detected_emis)} EMI loan patterns.",
            "user_id": str_user_id,
            "detected_count": len(detected_emis),
            "updated_transactions_count": len(updated_tx_ids),
            "detected_emis": detected_emis
        }
