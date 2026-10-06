from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.security import get_current_user, get_supabase_client
from app.schemas.emi import EMICreate
from app.schemas.subscription import SubscriptionCreate
from app.services.bank_detection_service import BankDetectionService
from app.services.demo_bank_service import DemoBankService
from app.services.emi_service import EMIService
from app.services.subscription_service import SubscriptionService
from app.services.transaction_store import SOURCE_DEMO, TransactionStore, clean_user_id

router = APIRouter(prefix="/bank", tags=["Bank Data & Detected Payments"])


def _uid(current_user: Any) -> str:
    raw = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    uid = clean_user_id(raw)
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid user.")
    return uid


def _pending_count(uid: str) -> int:
    res = (
        get_supabase_client().from_("detected_items")
        .select("id", count="exact").eq("user_id", uid).eq("status", "pending").limit(1).execute()
    )
    return res.count or 0


@router.get("/status", summary="Demo-data and review-list status for the signed-in user")
def bank_status(current_user: dict = Depends(get_current_user)):
    uid = _uid(current_user)
    demo_count = TransactionStore.count_by_source(uid, SOURCE_DEMO)
    return {
        "demo_loaded": demo_count > 0,
        "demo_transactions": demo_count,
        "pending_review": _pending_count(uid),
    }


@router.post("/demo/load", summary="Load sandbox demo bank data and run detection")
def load_demo(current_user: dict = Depends(get_current_user)):
    uid = _uid(current_user)
    added = DemoBankService.sync(uid)
    detection = BankDetectionService.run(uid)
    return {"added": added, "pending_review": detection["pending"], "new_items": detection["new"]}


@router.delete("/demo", summary="Remove sandbox demo bank data")
def remove_demo(current_user: dict = Depends(get_current_user)):
    uid = _uid(current_user)
    removed = DemoBankService.remove(uid)
    detection = BankDetectionService.run(uid)
    return {"removed": removed, "pending_review": detection["pending"]}


@router.post("/detect", summary="Re-run detection on the stored transactions")
def run_detection(current_user: dict = Depends(get_current_user)):
    return BankDetectionService.run(_uid(current_user))


@router.get("/transactions", summary="Recent bank activity (all sources)")
def list_transactions(limit: int = Query(100, ge=1, le=500), current_user: dict = Depends(get_current_user)):
    uid = _uid(current_user)
    rows = TransactionStore.get_user_transactions(uid)[:limit]
    return {"count": len(rows), "transactions": rows}


@router.get("/detected", summary="Payments the detector found, for the user to review")
def list_detected(status: str = Query("pending"), current_user: dict = Depends(get_current_user)):
    uid = _uid(current_user)
    res = (
        get_supabase_client().from_("detected_items").select("*")
        .eq("user_id", uid).eq("status", status).order("kind").order("merchant_name").execute()
    )
    return {"count": len(res.data or []), "items": res.data or []}


class ConfirmOverrides(BaseModel):
    amount: Optional[float] = None
    total_installments: Optional[int] = None
    installments_paid: Optional[int] = None
    next_date: Optional[date] = None


def _load_pending(uid: str, item_id: str) -> Dict[str, Any]:
    res = get_supabase_client().from_("detected_items").select("*").eq("id", item_id).eq("user_id", uid).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Detected item not found.")
    item = res.data[0]
    if item["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"This item was already {item['status']}.")
    return item


def _mark(item_id: str, status: str, created_id: Optional[str] = None) -> None:
    update = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    if created_id:
        update["created_item_id"] = str(created_id)
    get_supabase_client().from_("detected_items").update(update).eq("id", item_id).execute()


@router.post("/detected/{item_id}/confirm", summary="Confirm a detected payment and add it to the app")
def confirm_detected(item_id: str, overrides: Optional[ConfirmOverrides] = None, current_user: dict = Depends(get_current_user)):
    uid = _uid(current_user)
    item = _load_pending(uid, item_id)
    o = overrides or ConfirmOverrides()
    details = item.get("details") or {}
    amount = o.amount if o.amount and o.amount > 0 else float(item["amount"])
    next_date = o.next_date or (date.fromisoformat(str(item["next_date"])[:10]) if item.get("next_date") else date.today())

    first_date = date.fromisoformat(details["first_date"]) if details.get("first_date") else None

    if item["kind"] == "emi":
        total = o.total_installments or details.get("total_installments")
        if not total or total < 1:
            raise HTTPException(status_code=422, detail="Please enter the total number of installments for this EMI.")
        paid = o.installments_paid if o.installments_paid is not None else int(details.get("installments_paid") or 0)
        if paid > total:
            raise HTTPException(status_code=422, detail="Installments paid cannot be more than the total.")
        created = EMIService.create_emi(
            user_id=uid,
            payload=EMICreate(
                loan_name=item["merchant_name"],
                total_installments=int(total),
                installments_paid=paid,
                installment_amount=amount,
                start_date=first_date,
                next_due_date=next_date,
                status="completed" if paid >= total else "active",
            ),
        )
    else:
        created = SubscriptionService.create_subscription(
            db=None,
            user_id=uid,
            payload=SubscriptionCreate(
                merchant_name=item["merchant_name"],
                category=details.get("category") or "General",
                amount=amount,
                billing_frequency=item.get("billing_frequency") or "monthly",
                start_date=first_date,
                next_payment_date=next_date,
                status="active",
                is_recurring=True,
                autopay_enabled=True,
                source="detected",
            ),
        )

    _mark(item_id, "confirmed", (created or {}).get("id"))
    return {"status": "confirmed", "kind": item["kind"], "created": created}


@router.post("/detected/{item_id}/ignore", summary="Ignore a detected payment")
def ignore_detected(item_id: str, current_user: dict = Depends(get_current_user)):
    uid = _uid(current_user)
    _load_pending(uid, item_id)
    _mark(item_id, "ignored")
    return {"status": "ignored"}
