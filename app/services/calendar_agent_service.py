import json
import time
import threading
from datetime import date, datetime
from typing import Dict, Any, Optional, List

from app.services.google_calendar_service import GoogleCalendarService
from app.services.audit_log_service import AuditLoggerService
from app.core.security import get_supabase_client

_sync_locks: Dict[str, threading.RLock] = {}
_sync_locks_mutex = threading.Lock()

def _get_entity_lock(entity_id: str) -> threading.RLock:
    with _sync_locks_mutex:
        if entity_id not in _sync_locks:
            _sync_locks[entity_id] = threading.RLock()
        return _sync_locks[entity_id]

class CalendarAgentService:
    """
    Automatic Canonical Calendar Sync Layer.
    Decides and executes CREATE, UPDATE, and DELETE calendar operations automatically
    via official Google Calendar REST API using OAuth 2.0 refresh tokens.
    
    Idempotency: Uses `calendar_event_id` & `extendedProperties.private` metadata tagging.
    Concurrency: Uses per-entity mutex locking to prevent duplicate parallel syncs.
    Database Integrity: Keeps Supabase PostgreSQL strictly updated after each operation.
    """

    @staticmethod
    def handle_command(command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes internal agent commands.
        """
        action = command.get("action")
        item_type = command.get("type", "SUBSCRIPTION")
        user_id = command.get("user_id")
        payload = command.get("payload", {})

        if not user_id:
            return {"status": "FAILED", "reason": "Missing user_id"}

        if item_type == "SUBSCRIPTION":
            if action in ["CREATE_CALENDAR_EVENT", "CREATE"]:
                return CalendarAgentService.sync_subscription_create(user_id, payload)
            elif action in ["UPDATE_CALENDAR_EVENT", "UPDATE"]:
                return CalendarAgentService.sync_subscription_update(user_id, payload)
            elif action in ["DELETE_CALENDAR_EVENT", "DELETE"]:
                sub_id = payload.get("id") or payload.get("subscription_id")
                return CalendarAgentService.sync_subscription_delete(
                    user_id, sub_id, merchant_name=payload.get("merchant_name"), calendar_event_id=payload.get("calendar_event_id")
                )
        elif item_type == "EMI":
            if action in ["CREATE_CALENDAR_EVENT", "CREATE"]:
                return CalendarAgentService.sync_emi_create(user_id, payload)
            elif action in ["UPDATE_CALENDAR_EVENT", "UPDATE"]:
                return CalendarAgentService.sync_emi_update(user_id, payload)
            elif action in ["DELETE_CALENDAR_EVENT", "DELETE"]:
                emi_id = payload.get("id") or payload.get("emi_id")
                return CalendarAgentService.sync_emi_delete(
                    user_id, emi_id, loan_name=payload.get("loan_name"), calendar_event_id=payload.get("calendar_event_id")
                )

        return {"status": "FAILED", "reason": f"Unsupported action: {action}"}

    # ── CANONICAL LIFE CYCLE CONTRACT FUNCTIONS ──

    @staticmethod
    def sync_subscription_create(user_id: str, sub: Dict[str, Any]) -> Dict[str, Any]:
        """
        Canonical Sync on Subscription Create.
        Creates Google Calendar event tagged with privateExtendedProperty metadata.
        Updates DB with calendar_event_id and calendar_sync_status.
        """
        sub_id = str(sub.get("id") or "")
        lock = _get_entity_lock(f"sub_{sub_id}")
        with lock:
            # 1. Idempotency Check: does this subscription already have a calendar_event_id?
            existing_event_id = sub.get("calendar_event_id")
            if not existing_event_id and sub_id:
                try:
                    supabase = get_supabase_client()
                    db_row = supabase.from_("subscriptions").select("calendar_event_id").eq("id", sub_id).execute()
                    if db_row.data and len(db_row.data) > 0 and db_row.data[0].get("calendar_event_id"):
                        existing_event_id = db_row.data[0].get("calendar_event_id")
                except Exception:
                    pass

            if existing_event_id:
                print(f"🔒 Idempotency check: Subscription '{sub_id}' already has calendar_event_id ({existing_event_id}). Updating instead of creating duplicate.")
                sub["calendar_event_id"] = existing_event_id
                return CalendarAgentService.sync_subscription_update(user_id, sub)

            merchant = sub.get("merchant_name") or sub.get("name") or "Subscription"
            amount = float(sub.get("amount") or 0.0)
            freq = sub.get("billing_frequency") or sub.get("billing_cycle") or "monthly"
            autopay_enabled = sub.get("autopay_enabled", True)
            status = str(sub.get("status") or "active").lower()

            if not autopay_enabled or status in ["cancelled", "paid"]:
                print(f"Skipping calendar creation for '{merchant}': Autopay OFF or status is {status}")
                return {"status": "SKIPPED", "reason": "Autopay OFF or inactive status"}

            is_trial = status == "trial" or bool(sub.get("is_free_trial")) or bool(sub.get("trial_end_date"))
            trial_end = sub.get("trial_end_date")
            expected_first_pay = sub.get("expected_first_payment_date")

            if is_trial and trial_end:
                date_raw = trial_end
            else:
                date_raw = sub.get("next_payment_date") or sub.get("next_renewal_date") or sub.get("start_date") or str(date.today())

            try:
                event_date_obj = datetime.strptime(str(date_raw)[:10], "%Y-%m-%d").date()
            except Exception:
                event_date_obj = date.today()

            title = f"⚠️ {merchant} Trial Ending — ₹{amount:,.0f}" if is_trial else f"🔴 {merchant} Autopay — ₹{amount:,.0f}"

            if is_trial:
                description = (
                    f"Autopay Guard — Free Trial Expiration Alert\n\n"
                    f"Merchant: {merchant}\n"
                    f"Trial Ends On: {event_date_obj}\n"
                    f"Expected First Charge: ₹{amount:,.2f} on {expected_first_pay or event_date_obj}\n"
                    f"Billing Frequency: {freq}\n\n"
                    f"Cancel before {event_date_obj} if you do not wish to be billed automatically.\n"
                    f"Managed by Autopay Guard System"
                )
            else:
                description = (
                    f"Autopay Protection Alert\n\n"
                    f"Merchant: {merchant}\n"
                    f"Amount: ₹{amount:,.2f}\n"
                    f"Type: {freq} Subscription\n"
                    f"Expected Payment Date: {event_date_obj}\n\n"
                    f"Managed by Autopay Guard System"
                )

            private_props = {
                "source": "autopay_guard",
                "user_id": str(user_id),
                "entity_type": "subscription",
                "subscription_id": sub_id,
                "is_trial": "true" if is_trial else "false"
            }

            try:
                res = GoogleCalendarService.create_calendar_event(
                    user_id=user_id,
                    title=title,
                    event_date=event_date_obj,
                    description=description,
                    amount=amount,
                    private_props=private_props,
                    calendar_id=sub.get("calendar_id", "primary")
                )
            except Exception as call_err:
                res = {"status": "FAILED", "success": False, "error": str(call_err)}

            is_failed = res.get("status") == "FAILED" or res.get("success") is False or bool(res.get("error"))
            now_iso = datetime.utcnow().isoformat()

            if is_failed:
                sync_status = "FAILED"
                sync_error = str(res.get("error") or res.get("message") or "Google Calendar API error")
                event_id = None
            else:
                event_id = res.get("event_id")
                sync_status = "SYNCED" if event_id and not str(event_id).startswith("sim-") else "PENDING"
                sync_error = None

            if sub_id:
                try:
                    supabase = get_supabase_client()
                    update_data = {
                        "calendar_event_id": event_id,
                        "calendar_sync_status": sync_status
                    }
                    try:
                        supabase.from_("subscriptions").update({
                            **update_data,
                            "calendar_sync_error": sync_error
                        }).eq("id", sub_id).execute()
                    except Exception:
                        supabase.from_("subscriptions").update(update_data).eq("id", sub_id).execute()
                except Exception as e:
                    print("Supabase update subscription calendar_event_id error:", e)

            AuditLoggerService.log_action(user_id, "CALENDAR_EVENT_CREATE", details={"merchant": merchant, "event_id": event_id, "status": sync_status, "error": sync_error})

            if sync_status == "FAILED":
                return {
                    "status": "FAILED",
                    "calendar_event_id": None,
                    "calendar_sync_status": "FAILED",
                    "calendar_sync_error": sync_error,
                    "message": sync_error
                }

            return {
                "status": "SUCCESS",
                "calendar_event_id": event_id,
                "calendar_sync_status": sync_status,
                "calendar_sync_error": None,
                "message": res.get("message")
            }

    @staticmethod
    def sync_subscription_update(user_id: str, sub: Dict[str, Any], old_sub: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Canonical Sync on Subscription Update (including Autopay ON/OFF toggling and Trial rollover).
        If Autopay OFF, wipes event cleanly.
        If Autopay ON, creates or patches existing event.
        """
        sub_id = str(sub.get("id") or "")
        lock = _get_entity_lock(f"sub_{sub_id}")
        with lock:
            autopay_enabled = sub.get("autopay_enabled", True)
            status = str(sub.get("status") or "active").lower()

            if not autopay_enabled or status in ["cancelled", "paid"]:
                print(f"Autopay OFF or status '{status}' for subscription {sub_id}. Wiping calendar event cleanly.")
                return CalendarAgentService.sync_subscription_delete(
                    user_id=user_id,
                    sub_id=sub_id,
                    merchant_name=sub.get("merchant_name"),
                    calendar_event_id=sub.get("calendar_event_id")
                )

            is_trial = status == "trial" or bool(sub.get("is_free_trial"))
            trial_end = sub.get("trial_end_date")
            expected_first_pay = sub.get("expected_first_payment_date")

            date_raw = sub.get("next_payment_date") or sub.get("next_renewal_date") or (trial_end if is_trial else None) or sub.get("start_date") or str(date.today())

            try:
                event_date_obj = datetime.strptime(str(date_raw)[:10], "%Y-%m-%d").date()
            except Exception:
                event_date_obj = date.today()

            private_props = {
                "source": "autopay_guard",
                "user_id": str(user_id),
                "entity_type": "subscription",
                "subscription_id": sub_id,
                "is_trial": "true" if is_trial else "false"
            }

            event_id = sub.get("calendar_event_id")
            if not event_id:
                event_id = GoogleCalendarService.find_event_by_metadata(user_id, private_props)

            merchant = sub.get("merchant_name") or sub.get("name") or "Subscription"
            amount = float(sub.get("amount") or 0.0)
            freq = sub.get("billing_frequency") or sub.get("billing_cycle") or "monthly"

            title = f"⚠️ {merchant} Trial Ending — ₹{amount:,.0f}" if is_trial else f"🔴 {merchant} Autopay — ₹{amount:,.0f}"

            if is_trial:
                description = (
                    f"Autopay Guard — Free Trial Expiration Alert (Updated)\n\n"
                    f"Merchant: {merchant}\n"
                    f"Trial Ends On: {event_date_obj}\n"
                    f"Expected First Charge: ₹{amount:,.2f} on {expected_first_pay or event_date_obj}\n"
                    f"Billing Frequency: {freq}\n\n"
                    f"Managed by Autopay Guard System"
                )
            else:
                description = (
                    f"Autopay Protection Alert (Updated)\n\n"
                    f"Merchant: {merchant}\n"
                    f"Amount: ₹{amount:,.2f}\n"
                    f"Type: {freq} Subscription\n"
                    f"Expected Payment Date: {event_date_obj}\n\n"
                    f"Managed by Autopay Guard System"
                )

            try:
                if event_id:
                    res = GoogleCalendarService.patch_calendar_event(
                        user_id=user_id,
                        event_id=event_id,
                        summary=title,
                        event_date=event_date_obj,
                        description=description,
                        amount=amount,
                        private_props=private_props,
                        calendar_id=sub.get("calendar_id", "primary")
                    )
                    updated_id = res.get("event_id") or event_id
                else:
                    # Create real event on Google Calendar
                    res = GoogleCalendarService.create_calendar_event(
                        user_id=user_id,
                        title=title,
                        event_date=event_date_obj,
                        description=description,
                        amount=amount,
                        private_props=private_props,
                        calendar_id=sub.get("calendar_id", "primary")
                    )
                    updated_id = res.get("event_id")
            except Exception as call_err:
                res = {"status": "FAILED", "success": False, "error": str(call_err)}
                updated_id = event_id

            is_failed = res.get("status") == "FAILED" or res.get("success") is False or bool(res.get("error"))

            if is_failed:
                sync_status = "FAILED"
                sync_error = str(res.get("error") or res.get("message") or "Google Calendar update failed")
            else:
                sync_status = "SYNCED" if updated_id and not str(updated_id).startswith("sim-") else "PENDING"
                sync_error = None

            if sub_id:
                try:
                    supabase = get_supabase_client()
                    update_data = {
                        "calendar_event_id": updated_id if sync_status != "FAILED" else event_id,
                        "calendar_sync_status": sync_status
                    }
                    try:
                        supabase.from_("subscriptions").update({
                            **update_data,
                            "calendar_sync_error": sync_error
                        }).eq("id", sub_id).execute()
                    except Exception:
                        supabase.from_("subscriptions").update(update_data).eq("id", sub_id).execute()
                except Exception as e:
                    print("Supabase update subscription calendar_event_id error:", e)

            AuditLoggerService.log_action(user_id, "CALENDAR_EVENT_UPDATE", details={"merchant": merchant, "event_id": updated_id, "status": sync_status, "error": sync_error})

            if sync_status == "FAILED":
                return {
                    "status": "FAILED",
                    "calendar_event_id": updated_id,
                    "calendar_sync_status": "FAILED",
                    "calendar_sync_error": sync_error,
                    "message": sync_error
                }

            return {"status": "SUCCESS", "calendar_event_id": updated_id, "calendar_sync_status": sync_status, "calendar_sync_error": None}

    @staticmethod
    def sync_subscription_delete(
        user_id: str,
        sub_id: str,
        merchant_name: Optional[str] = None,
        calendar_event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Canonical Sync on Subscription Delete / Autopay OFF.
        Purges event by ID or metadata. Sets calendar_event_id = NULL in DB.
        """
        sub_id = str(sub_id or "")
        lock = _get_entity_lock(f"sub_{sub_id}")
        with lock:
            private_props = {
                "source": "autopay_guard",
                "user_id": str(user_id),
                "entity_type": "subscription",
                "subscription_id": sub_id
            }

            res = GoogleCalendarService.delete_event_by_id_or_metadata(
                user_id=user_id,
                event_id=calendar_event_id,
                private_props=private_props
            )

            if sub_id:
                try:
                    supabase = get_supabase_client()
                    supabase.from_("subscriptions").update({
                        "calendar_event_id": None,
                        "calendar_sync_status": "PENDING"
                    }).eq("id", sub_id).execute()
                except Exception as e:
                    print("Supabase clear subscription calendar_event_id note:", e)

            AuditLoggerService.log_action(user_id, "CALENDAR_EVENT_DELETE", details={"subscription_id": sub_id, "merchant": merchant_name})
            return {"status": "SUCCESS", "calendar_event_id": None, "calendar_sync_status": "PENDING", "message": res.get("message")}

    @staticmethod
    def sync_emi_create(user_id: str, emi: Dict[str, Any]) -> Dict[str, Any]:
        """
        Canonical Sync on EMI Create.
        """
        emi_id = str(emi.get("id") or "")
        lock = _get_entity_lock(f"emi_{emi_id}")
        with lock:
            # 1. Idempotency Check: does this EMI already have a calendar_event_id?
            existing_event_id = emi.get("calendar_event_id")
            if not existing_event_id and emi_id:
                try:
                    supabase = get_supabase_client()
                    db_row = supabase.from_("emis").select("calendar_event_id").eq("id", emi_id).execute()
                    if db_row.data and len(db_row.data) > 0 and db_row.data[0].get("calendar_event_id"):
                        existing_event_id = db_row.data[0].get("calendar_event_id")
                except Exception:
                    pass

            private_props = {
                "source": "autopay_guard",
                "user_id": str(user_id),
                "entity_type": "emi",
                "emi_id": emi_id
            }

            if not existing_event_id:
                existing_event_id = GoogleCalendarService.find_event_by_metadata(user_id, private_props)

            if existing_event_id:
                print(f"🔒 Idempotency check: EMI '{emi_id}' already has calendar_event_id ({existing_event_id}). Updating/skipping duplicate creation.")
                emi["calendar_event_id"] = existing_event_id
                return CalendarAgentService.sync_emi_update(user_id, emi)

            name = emi.get("loan_name") or emi.get("lender_name") or "EMI Loan"
            amount = float(emi.get("installment_amount") or 0.0)
            status = str(emi.get("status") or "active").lower()

            if status in ["cancelled", "paid"]:
                return {"status": "SKIPPED", "reason": "Inactive EMI status"}

            date_raw = emi.get("next_due_date") or str(date.today())
            try:
                event_date_obj = datetime.strptime(str(date_raw)[:10], "%Y-%m-%d").date()
            except Exception:
                event_date_obj = date.today()

            title = f"💳 {name} EMI — ₹{amount:,.0f}"
            description = (
                f"Autopay Guard Protection Alert — EMI Loan Installment\n\n"
                f"Loan/Lender: {name}\n"
                f"Installment Amount: ₹{amount:,.2f}\n"
                f"Due Date: {event_date_obj}\n"
                f"Installments Paid: {emi.get('installments_paid', 0)}/{emi.get('total_installments', 0)}\n\n"
                f"Managed by Autopay Guard System"
            )

            try:
                res = GoogleCalendarService.create_calendar_event(
                    user_id=user_id,
                    title=title,
                    event_date=event_date_obj,
                    description=description,
                    amount=amount,
                    private_props=private_props,
                    calendar_id=emi.get("calendar_id", "primary")
                )
            except Exception as call_err:
                res = {"status": "FAILED", "success": False, "error": str(call_err)}

            is_failed = res.get("status") == "FAILED" or res.get("success") is False or bool(res.get("error"))
            now_iso = datetime.utcnow().isoformat()

            if is_failed:
                sync_status = "FAILED"
                sync_error = str(res.get("error") or res.get("message") or "Google Calendar API error")
                event_id = None
            else:
                event_id = res.get("event_id")
                sync_status = "SYNCED" if event_id and not str(event_id).startswith("sim-") else "PENDING"
                sync_error = None

            if emi_id:
                try:
                    supabase = get_supabase_client()
                    update_data = {
                        "calendar_event_id": event_id,
                        "calendar_sync_status": sync_status
                    }
                    try:
                        supabase.from_("emis").update({
                            **update_data,
                            "calendar_sync_error": sync_error
                        }).eq("id", emi_id).execute()
                    except Exception:
                        supabase.from_("emis").update(update_data).eq("id", emi_id).execute()
                except Exception as e:
                    print("Supabase update EMI calendar_event_id error:", e)

            if sync_status == "FAILED":
                return {
                    "status": "FAILED",
                    "calendar_event_id": None,
                    "calendar_sync_status": "FAILED",
                    "calendar_sync_error": sync_error,
                    "message": sync_error
                }

            return {
                "status": "SUCCESS",
                "calendar_event_id": event_id,
                "calendar_sync_status": sync_status,
                "calendar_sync_error": None,
                "message": res.get("message")
            }

    @staticmethod
    def sync_emi_update(user_id: str, emi: Dict[str, Any], old_emi: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Canonical Sync on EMI Update.
        """
        emi_id = str(emi.get("id") or "")
        lock = _get_entity_lock(f"emi_{emi_id}")
        with lock:
            status = str(emi.get("status") or "active").lower()
            total_inst = int(emi.get("total_installments") or 1)
            paid_inst = int(emi.get("installments_paid") or 0)
            is_completed = (status in ["cancelled", "paid", "completed"]) or (paid_inst >= total_inst)

            if is_completed:
                print(f"EMI {emi_id} is completed ({paid_inst}/{total_inst}) or status '{status}'. Purging calendar event cleanly.")
                return CalendarAgentService.sync_emi_delete(
                    user_id=user_id,
                    emi_id=emi_id,
                    loan_name=emi.get("loan_name"),
                    calendar_event_id=emi.get("calendar_event_id")
                )

            event_id = emi.get("calendar_event_id")
            private_props = {
                "source": "autopay_guard",
                "user_id": str(user_id),
                "entity_type": "emi",
                "emi_id": emi_id,
                "is_completed": "true" if is_completed else "false"
            }
            if not event_id:
                event_id = GoogleCalendarService.find_event_by_metadata(user_id, private_props)

            name = emi.get("loan_name") or emi.get("lender_name") or "EMI Loan"
            amount = float(emi.get("installment_amount") or 0.0)
            date_raw = emi.get("next_due_date") or str(date.today())
            try:
                event_date_obj = datetime.strptime(str(date_raw)[:10], "%Y-%m-%d").date()
            except Exception:
                event_date_obj = date.today()

            if is_completed:
                title = f"✅ {name} EMI (Completed) — ₹{amount:,.0f}"
                description = (
                    f"Autopay Guard — EMI Loan Fully Paid & Completed\n\n"
                    f"Loan/Lender: {name}\n"
                    f"Total Installments Paid: {paid_inst}/{total_inst} (100%)\n"
                    f"Completion Date: {event_date_obj}\n\n"
                    f"Status: ✅ COMPLETED\n"
                    f"Managed by Autopay Guard System"
                )
            else:
                title = f"💳 {name} EMI — ₹{amount:,.0f}"
                description = (
                    f"Autopay Guard Protection Alert — EMI Loan Installment (Updated)\n\n"
                    f"Loan/Lender: {name}\n"
                    f"Installment Amount: ₹{amount:,.2f}\n"
                    f"Due Date: {event_date_obj}\n"
                    f"Installments Paid: {paid_inst}/{total_inst}\n\n"
                    f"Managed by Autopay Guard System"
                )

            try:
                if event_id:
                    res = GoogleCalendarService.patch_calendar_event(
                        user_id=user_id,
                        event_id=event_id,
                        summary=title,
                        event_date=event_date_obj,
                        description=description,
                        amount=amount,
                        private_props=private_props,
                        calendar_id=emi.get("calendar_id", "primary")
                    )
                    updated_id = res.get("event_id") or event_id
                else:
                    # Create real event on Google Calendar
                    res = GoogleCalendarService.create_calendar_event(
                        user_id=user_id,
                        title=title,
                        event_date=event_date_obj,
                        description=description,
                        amount=amount,
                        private_props=private_props,
                        calendar_id=emi.get("calendar_id", "primary")
                    )
                    updated_id = res.get("event_id")
            except Exception as call_err:
                res = {"status": "FAILED", "success": False, "error": str(call_err)}
                updated_id = event_id

            is_failed = res.get("status") == "FAILED" or res.get("success") is False or bool(res.get("error"))

            if is_failed:
                sync_status = "FAILED"
                sync_error = str(res.get("error") or res.get("message") or "Google Calendar update failed")
            else:
                sync_status = "SYNCED" if updated_id and not str(updated_id).startswith("sim-") else "PENDING"
                sync_error = None

            if emi_id:
                try:
                    supabase = get_supabase_client()
                    update_data = {
                        "calendar_event_id": updated_id if sync_status != "FAILED" else event_id,
                        "calendar_sync_status": sync_status
                    }
                    try:
                        supabase.from_("emis").update({
                            **update_data,
                            "calendar_sync_error": sync_error
                        }).eq("id", emi_id).execute()
                    except Exception:
                        supabase.from_("emis").update(update_data).eq("id", emi_id).execute()
                except Exception as e:
                    print("Supabase update EMI calendar_event_id error:", e)

            if sync_status == "FAILED":
                return {
                    "status": "FAILED",
                    "calendar_event_id": updated_id,
                    "calendar_sync_status": "FAILED",
                    "calendar_sync_error": sync_error,
                    "message": sync_error
                }

            return {"status": "SUCCESS", "calendar_event_id": updated_id, "calendar_sync_status": sync_status, "calendar_sync_error": None}

    @staticmethod
    def sync_emi_delete(
        user_id: str,
        emi_id: str,
        loan_name: Optional[str] = None,
        calendar_event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Canonical Sync on EMI Delete.
        """
        emi_id = str(emi_id or "")
        lock = _get_entity_lock(f"emi_{emi_id}")
        with lock:
            private_props = {
                "source": "autopay_guard",
                "user_id": str(user_id),
                "entity_type": "emi",
                "emi_id": emi_id
            }

            res = GoogleCalendarService.delete_event_by_id_or_metadata(
                user_id=user_id,
                event_id=calendar_event_id,
                private_props=private_props
            )

            if emi_id:
                try:
                    supabase = get_supabase_client()
                    supabase.from_("emis").update({
                        "calendar_event_id": None,
                        "calendar_sync_status": "PENDING"
                    }).eq("id", emi_id).execute()
                except Exception as e:
                    print("Supabase clear EMI calendar_event_id note:", e)

            return {"status": "SUCCESS", "calendar_event_id": None, "calendar_sync_status": "PENDING", "message": res.get("message")}

    # ── BACKWARD COMPATIBLE ALIASES ──

    @staticmethod
    def create_subscription_event(user_id: str, sub: Dict[str, Any]) -> Dict[str, Any]:
        return CalendarAgentService.sync_subscription_create(user_id, sub)

    @staticmethod
    def update_subscription_event(user_id: str, sub: Dict[str, Any]) -> Dict[str, Any]:
        return CalendarAgentService.sync_subscription_update(user_id, sub)

    @staticmethod
    def delete_subscription_event(user_id: str, sub: Dict[str, Any]) -> Dict[str, Any]:
        sub_id = sub.get("id") or sub.get("subscription_id")
        return CalendarAgentService.sync_subscription_delete(
            user_id, sub_id, merchant_name=sub.get("merchant_name"), calendar_event_id=sub.get("calendar_event_id")
        )

    @staticmethod
    def create_emi_event(user_id: str, emi: Dict[str, Any]) -> Dict[str, Any]:
        return CalendarAgentService.sync_emi_create(user_id, emi)

    @staticmethod
    def update_emi_event(user_id: str, emi: Dict[str, Any]) -> Dict[str, Any]:
        return CalendarAgentService.sync_emi_update(user_id, emi)

    @staticmethod
    def delete_emi_event(user_id: str, emi: Dict[str, Any]) -> Dict[str, Any]:
        emi_id = emi.get("id") or emi.get("emi_id")
        return CalendarAgentService.sync_emi_delete(
            user_id, emi_id, loan_name=emi.get("loan_name"), calendar_event_id=emi.get("calendar_event_id")
        )

    # ── FULL DATABASE RESYNC SERVICE ──

    @staticmethod
    def resync_user_calendar(user_id: str) -> Dict[str, Any]:
        """
        Full database-driven calendar resynchronization service.
        Iterates over all active subscriptions and EMIs in DB and executes canonical sync methods.
        """
        from app.services.subscription_service import SubscriptionService
        from app.services.emi_service import EMIService

        clean_uid = str(user_id).strip('"\'')

        print(f"\n{'='*60}")
        print(f"🔄 RESYNC START for user: {clean_uid}")
        print(f"{'='*60}")

        subs = SubscriptionService.get_user_subscriptions(clean_uid)
        emis = EMIService.get_user_emis(clean_uid)

        created_count = 0
        updated_count = 0
        removed_count = 0

        for s in subs:
            autopay_on = s.get("autopay_enabled", True)
            status = str(s.get("status") or "active").lower()

            if not autopay_on or status in ["cancelled", "paid"]:
                sub_id = s.get("id")
                res = CalendarAgentService.sync_subscription_delete(
                    clean_uid, sub_id, merchant_name=s.get("merchant_name"), calendar_event_id=s.get("calendar_event_id")
                )
                removed_count += 1
            else:
                res = CalendarAgentService.sync_subscription_update(clean_uid, s)
                if res.get("status") == "SUCCESS":
                    created_count += 1

        for e in emis:
            status = str(e.get("status") or "active").lower()

            if status in ["cancelled", "completed", "paid"]:
                emi_id = e.get("id")
                res = CalendarAgentService.sync_emi_delete(
                    clean_uid, emi_id, loan_name=e.get("loan_name"), calendar_event_id=e.get("calendar_event_id")
                )
                removed_count += 1
            else:
                res = CalendarAgentService.sync_emi_update(clean_uid, e)
                if res.get("status") == "SUCCESS":
                    created_count += 1

        print(f"\n{'='*60}")
        print(f"🔄 RESYNC COMPLETE: {created_count} processed, {removed_count} removed")
        print(f"{'='*60}\n")

        AuditLoggerService.log_action(clean_uid, "CALENDAR_RESYNC_ALL", details={
            "created_or_updated": created_count,
            "removed": removed_count
        })

        return {
            "success": True,
            "user_id": clean_uid,
            "subscriptions_found": len(subs),
            "emis_found": len(emis),
            "events_created": created_count,
            "events_updated": updated_count,
            "events_deleted": removed_count,
            "status": "SYNCED",
            "message": f"Calendar synchronization complete: {created_count} processed, {removed_count} removed."
        }

    # ── RETRY MECHANISM (HYBRID: MANUAL CARD ACTION + BACKGROUND AUTO-RETRY) ──

    @staticmethod
    def retry_subscription_sync(user_id: str, sub_id: str) -> Dict[str, Any]:
        """
        Retries calendar sync for a specific failed subscription.
        """
        from app.services.subscription_service import SubscriptionService
        clean_uid = str(user_id).strip('"\'')
        sub = SubscriptionService.get_subscription_by_id(clean_uid, sub_id)
        if not sub:
            return {"status": "FAILED", "success": False, "message": f"Subscription '{sub_id}' not found."}

        print(f"🔄 Retrying calendar sync for subscription: {sub.get('merchant_name')} ({sub_id})")
        return CalendarAgentService.sync_subscription_update(clean_uid, sub)

    @staticmethod
    def retry_emi_sync(user_id: str, emi_id: str) -> Dict[str, Any]:
        """
        Retries calendar sync for a specific failed EMI.
        """
        from app.services.emi_service import EMIService
        clean_uid = str(user_id).strip('"\'')
        emi = EMIService.get_emi_by_id(clean_uid, emi_id)
        if not emi:
            return {"status": "FAILED", "success": False, "message": f"EMI '{emi_id}' not found."}

        print(f"🔄 Retrying calendar sync for EMI: {emi.get('loan_name')} ({emi_id})")
        return CalendarAgentService.sync_emi_update(clean_uid, emi)

    @staticmethod
    def retry_all_failed_syncs(user_id: str) -> Dict[str, Any]:
        """
        Scans all failed subscriptions and EMIs for a user and attempts to sync each with Google Calendar.
        """
        from app.services.subscription_service import SubscriptionService
        from app.services.emi_service import EMIService

        clean_uid = str(user_id).strip('"\'')
        supabase = get_supabase_client()

        # 1. Fetch failed subscriptions
        failed_subs = []
        try:
            sub_res = supabase.from_("subscriptions").select("*").eq("user_id", clean_uid).ilike("calendar_sync_status", "failed").execute()
            failed_subs = sub_res.data or []
        except Exception as e:
            print("Supabase load failed subscriptions note:", e)

        # 2. Fetch failed EMIs
        failed_emis = []
        try:
            emi_res = supabase.from_("emis").select("*").eq("user_id", clean_uid).ilike("calendar_sync_status", "failed").execute()
            failed_emis = emi_res.data or []
        except Exception as e:
            print("Supabase load failed EMIs note:", e)

        subs_recovered = 0
        emis_recovered = 0
        still_failed = 0

        for s in failed_subs:
            res = CalendarAgentService.sync_subscription_update(clean_uid, s)
            if res.get("status") == "SUCCESS" and res.get("calendar_sync_status") == "SYNCED":
                subs_recovered += 1
            else:
                still_failed += 1

        for e in failed_emis:
            res = CalendarAgentService.sync_emi_update(clean_uid, e)
            if res.get("status") == "SUCCESS" and res.get("calendar_sync_status") == "SYNCED":
                emis_recovered += 1
            else:
                still_failed += 1

        AuditLoggerService.log_action(clean_uid, "CALENDAR_RETRY_ALL_FAILED", details={
            "failed_subs_total": len(failed_subs),
            "failed_emis_total": len(failed_emis),
            "subs_recovered": subs_recovered,
            "emis_recovered": emis_recovered,
            "still_failed": still_failed
        })

        return {
            "success": True,
            "user_id": clean_uid,
            "total_failed_found": len(failed_subs) + len(failed_emis),
            "subscriptions_recovered": subs_recovered,
            "emis_recovered": emis_recovered,
            "still_failed": still_failed,
            "message": f"Retry complete: {subs_recovered + emis_recovered} synced successfully, {still_failed} failed."
        }


