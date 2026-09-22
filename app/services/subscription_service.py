import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from app.core.security import get_supabase_client


class SubscriptionService:
    @staticmethod
    def create_subscription(db: Optional[Session], user_id: str, payload: SubscriptionCreate, trigger_calendar: bool = True) -> dict:
        sub_id = str(uuid.uuid4())
        clean_uid = str(user_id).strip('"\'')
        new_data = {
            "id": sub_id,
            "user_id": clean_uid,
            "merchant_name": payload.merchant_name,
            "category": payload.category or "General",
            "amount": float(payload.amount),
            "billing_frequency": payload.billing_frequency or "monthly",
            "start_date": str(payload.start_date) if payload.start_date else None,
            "next_payment_date": str(payload.next_payment_date),
            "status": payload.status or ("trial" if payload.is_free_trial else "active"),
            "is_recurring": payload.is_recurring if payload.is_recurring is not None else True,
            "autopay_enabled": payload.autopay_enabled if payload.autopay_enabled is not None else True,
            "trial_start_date": str(payload.trial_start_date) if payload.trial_start_date else None,
            "trial_end_date": str(payload.trial_end_date) if payload.trial_end_date else None,
            "expected_first_payment_date": str(payload.expected_first_payment_date) if payload.expected_first_payment_date else None,
            "is_free_trial": bool(payload.is_free_trial or (payload.status == "trial")),
            "risk_score": payload.risk_score or 10,
            "receipt_url": payload.receipt_url
        }

        # Write directly to Supabase PostgreSQL DB with duplicate check (upsert logic)
        supabase = get_supabase_client()
        created_sub = new_data
        try:
            # Check if record with same user_id and merchant_name already exists
            existing = supabase.from_("subscriptions").select("id").eq("user_id", clean_uid).ilike("merchant_name", payload.merchant_name.strip()).execute()
            if existing.data and len(existing.data) > 0:
                existing_id = existing.data[0]["id"]
                new_data["id"] = existing_id
                up_res = supabase.from_("subscriptions").update(new_data).eq("id", existing_id).execute()
                if up_res.data and len(up_res.data) > 0:
                    created_sub = {**new_data, **up_res.data[0]}
            else:
                res = supabase.from_("subscriptions").insert(new_data).execute()
                if res.data and len(res.data) > 0:
                    created_sub = {**new_data, **res.data[0]}
        except Exception as err:
            print("Supabase REST insert/upsert note (schema cache fallback):", err)
            core_keys = [
                "id", "user_id", "merchant_name", "category", "amount", 
                "billing_frequency", "start_date", "next_payment_date", 
                "status", "is_recurring", "autopay_enabled", "risk_score", 
                "receipt_url"
            ]
            fallback_data = {k: v for k, v in new_data.items() if k in core_keys}
            try:
                res = supabase.from_("subscriptions").insert(fallback_data).execute()
                if res.data and len(res.data) > 0:
                    created_sub = {**new_data, **res.data[0]}
            except Exception as e2:
                print("Supabase REST core insert error:", e2)

        # Trigger Automatic Calendar Agent if requested
        if trigger_calendar:
            try:
                from app.services.calendar_agent_service import CalendarAgentService
                cal_res = CalendarAgentService.handle_command({
                    "action": "CREATE_CALENDAR_EVENT",
                    "type": "SUBSCRIPTION",
                    "user_id": clean_uid,
                    "payload": created_sub
                })
                if cal_res:
                    created_sub["calendar_event_id"] = cal_res.get("calendar_event_id")
                    created_sub["calendar_sync_status"] = cal_res.get("calendar_sync_status", "PENDING")
                    created_sub["calendar_sync_error"] = cal_res.get("calendar_sync_error")
            except Exception as cal_err:
                print("Calendar Agent trigger error on create_subscription:", cal_err)
                created_sub["calendar_sync_status"] = "FAILED"
                created_sub["calendar_sync_error"] = str(cal_err)

        return created_sub

    @staticmethod
    def seed_initial_mock_subscriptions(user_id: str) -> List[dict]:
        """
        Seeds initial mock subscriptions for a new user directly into Supabase PostgreSQL.
        """
        from datetime import date, timedelta
        today = date.today()
        clean_uid = str(user_id).strip('"\'')
        
        default_items = [
            {"merchant_name": "Netflix Premium", "category": "Entertainment", "amount": 649.0, "billing_frequency": "monthly", "next_payment_date": str(today + timedelta(days=25)), "status": "active", "is_recurring": True, "autopay_enabled": True},
            {"merchant_name": "ChatGPT Plus", "category": "Software & AI", "amount": 1999.0, "billing_frequency": "monthly", "next_payment_date": str(today + timedelta(days=12)), "status": "active", "is_recurring": True, "autopay_enabled": True},
            {"merchant_name": "Notion AI (Free Trial)", "category": "Productivity", "amount": 899.0, "billing_frequency": "monthly", "next_payment_date": str(today + timedelta(days=18)), "status": "trial", "is_recurring": True, "autopay_enabled": True},
            {"merchant_name": "Spotify Premium", "category": "Entertainment", "amount": 179.0, "billing_frequency": "monthly", "next_payment_date": str(today + timedelta(days=15)), "status": "active", "is_recurring": True, "autopay_enabled": True},
            {"merchant_name": "Adobe Creative Cloud", "category": "Design & Work", "amount": 4230.0, "billing_frequency": "monthly", "next_payment_date": str(today + timedelta(days=8)), "status": "active", "is_recurring": True, "autopay_enabled": True},
            {"merchant_name": "GitHub Copilot", "category": "Software & AI", "amount": 8200.0, "billing_frequency": "yearly", "next_payment_date": str(today + timedelta(days=180)), "status": "active", "is_recurring": True, "autopay_enabled": True},
            {"merchant_name": "freefire", "category": "General", "amount": 20.0, "billing_frequency": "monthly", "next_payment_date": str(today + timedelta(days=5)), "status": "trial", "is_recurring": True, "autopay_enabled": True},
            {"merchant_name": "gym", "category": "Gym & Fitness", "amount": 100.0, "billing_frequency": "monthly", "next_payment_date": str(today + timedelta(days=3)), "status": "trial", "is_recurring": True, "autopay_enabled": True},
            {"merchant_name": "claude", "category": "Software & AI", "amount": 500.0, "billing_frequency": "monthly", "next_payment_date": str(today + timedelta(days=28)), "status": "trial", "is_recurring": True, "autopay_enabled": True},
            {"merchant_name": "my jio", "category": "Entertainment", "amount": 100.0, "billing_frequency": "monthly", "next_payment_date": str(today + timedelta(days=10)), "status": "trial", "is_recurring": True, "autopay_enabled": True}
        ]

        created = []
        for item in default_items:
            try:
                sub_data = SubscriptionService.create_subscription(
                    db=None,
                    user_id=clean_uid,
                    payload=SubscriptionCreate(**item),
                    trigger_calendar=False
                )
                created.append(sub_data)
            except Exception as e:
                print("Error seeding mock subscription item:", e)

        return created

    @staticmethod
    def get_user_subscriptions(user_id: str, status: Optional[str] = None, category: Optional[str] = None) -> List[dict]:
        clean_uid = str(user_id).strip('"\'')
        raw_subs = []
        supabase = get_supabase_client()

        # Query database directly for this user
        try:
            query = supabase.from_("subscriptions").select("*").eq("user_id", clean_uid)
            if status:
                query = query.eq("status", status)
            if category:
                query = query.eq("category", category)
            
            res = query.execute()
            if res.data and len(res.data) > 0:
                raw_subs = res.data
        except Exception as err:
            print("Supabase REST select error:", err)

        # FAST PATH: If user already has subscriptions, skip the expensive mock-init check entirely.
        # Only check mock_data_initialized when the query returned ZERO rows.
        if not raw_subs:
            from app.services.mock_generator_service import MockGeneratorService
            if not MockGeneratorService.is_mock_data_initialized(clean_uid):
                MockGeneratorService.ensure_one_time_mock_initialization(clean_uid)
                try:
                    query = supabase.from_("subscriptions").select("*").eq("user_id", clean_uid)
                    if status:
                        query = query.eq("status", status)
                    if category:
                        query = query.eq("category", category)
                    res = query.execute()
                    if res.data:
                        raw_subs = res.data
                except Exception as err:
                    print("Supabase re-select after initialization error:", err)

        # Deduplicate subscriptions by merchant name (case-insensitive)
        unique_subs = []
        seen_merchants = set()
        for s in raw_subs:
            m_name = (s.get("merchant_name") or s.get("name") or "").strip().lower()
            if m_name:
                if m_name in seen_merchants:
                    continue
                seen_merchants.add(m_name)
            unique_subs.append(s)

        return unique_subs

    @staticmethod
    def get_subscription_by_id(user_id: str, sub_id: str) -> Optional[dict]:
        clean_uid = str(user_id).strip('"\'')
        clean_sid = str(sub_id).strip('"\'')

        supabase = get_supabase_client()
        
        # 1. Query Supabase Database by exact id AND user_id (strict DB-level scoping)
        try:
            res = supabase.from_("subscriptions").select("*").eq("id", clean_sid).eq("user_id", clean_uid).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as err:
            pass

        # 2. Query Supabase Database by user_id and match merchant_name or partial ID
        try:
            res = supabase.from_("subscriptions").select("*").eq("user_id", clean_uid).execute()
            if res.data:
                for item in res.data:
                    item_sid = str(item.get("id")).strip('"\'')
                    m_name = str(item.get("merchant_name") or item.get("name") or "").strip().lower()
                    if item_sid == clean_sid or clean_sid.lower() in m_name or m_name in clean_sid.lower():
                        return item
        except Exception as err:
            pass

        return None

    @staticmethod
    def update_subscription(user_id: str, sub_id: str, payload: SubscriptionUpdate) -> Optional[dict]:
        clean_uid = str(user_id).strip('"\'')
        clean_sid = str(sub_id).strip('"\'')

        # Retrieve ground truth record from Supabase database scoped to user
        existing = SubscriptionService.get_subscription_by_id(clean_uid, clean_sid)

        # Fallback if record not found by exact ID: fetch user subscriptions from database
        if not existing:
            m_name = payload.merchant_name if payload.merchant_name else None
            all_subs = SubscriptionService.get_user_subscriptions(clean_uid)
            if all_subs:
                for s in all_subs:
                    s_id = str(s.get("id")).strip('"\'')
                    s_m = str(s.get("merchant_name") or s.get("name") or "").strip().lower()
                    if s_id == clean_sid or (m_name and m_name.lower() in s_m):
                        existing = s
                        break

            if not existing:
                existing = {
                    "id": clean_sid,
                    "user_id": clean_uid,
                    "merchant_name": m_name or "Subscription",
                    "amount": 0.0,
                    "status": "active",
                    "autopay_enabled": True
                }

        update_data = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
        if "start_date" in update_data and update_data["start_date"]:
            update_data["start_date"] = str(update_data["start_date"])
        if "next_payment_date" in update_data and update_data["next_payment_date"]:
            update_data["next_payment_date"] = str(update_data["next_payment_date"])
        if "trial_start_date" in update_data and update_data["trial_start_date"]:
            update_data["trial_start_date"] = str(update_data["trial_start_date"])
        if "trial_end_date" in update_data and update_data["trial_end_date"]:
            update_data["trial_end_date"] = str(update_data["trial_end_date"])
        if "expected_first_payment_date" in update_data and update_data["expected_first_payment_date"]:
            update_data["expected_first_payment_date"] = str(update_data["expected_first_payment_date"])

        existing.update(update_data)
        actual_id = existing.get("id") or clean_sid
        merchant_key = (existing.get("merchant_name") or "").strip()

        # Update in Supabase database directly with user_id check
        supabase = get_supabase_client()
        try:
            res = supabase.from_("subscriptions").update(update_data).eq("id", actual_id).eq("user_id", clean_uid).execute()
            if res.data and len(res.data) > 0:
                existing = {**existing, **res.data[0]}
        except Exception as err:
            print("Supabase REST update note (schema cache fallback):", err)
            core_keys = [
                "merchant_name", "category", "amount", 
                "billing_frequency", "start_date", "next_payment_date", 
                "status", "is_recurring", "autopay_enabled", "risk_score", 
                "receipt_url", "calendar_event_id", "calendar_sync_status", "calendar_sync_error"
            ]
            fallback_data = {k: v for k, v in update_data.items() if k in core_keys}
            try:
                res = supabase.from_("subscriptions").update(fallback_data).eq("id", actual_id).eq("user_id", clean_uid).execute()
                if res.data and len(res.data) > 0:
                    existing = {**existing, **res.data[0]}
            except Exception as e2:
                print("Supabase REST core update error:", e2)

        # Trigger Calendar Agent with updated details from Supabase DB
        try:
            from app.services.calendar_agent_service import CalendarAgentService
            if existing.get("status") == "cancelled" or existing.get("autopay_enabled") == False:
                cal_res = CalendarAgentService.sync_subscription_delete(
                    user_id=clean_uid,
                    sub_id=actual_id,
                    merchant_name=existing.get("merchant_name"),
                    calendar_event_id=existing.get("calendar_event_id")
                )
                existing["calendar_event_id"] = None
            else:
                cal_res = CalendarAgentService.sync_subscription_update(
                    user_id=clean_uid,
                    sub=existing
                )
                if cal_res and "calendar_event_id" in cal_res:
                    existing["calendar_event_id"] = cal_res["calendar_event_id"]
        except Exception as cal_err:
            print("Calendar Agent trigger error on update_subscription:", cal_err)

        return existing

    @staticmethod
    def soft_delete_subscription(user_id: str, sub_id: str) -> Optional[dict]:
        clean_uid = str(user_id).strip('"\'')
        return SubscriptionService.update_subscription(clean_uid, sub_id, SubscriptionUpdate(status="cancelled", autopay_enabled=False))

    @staticmethod
    def delete_subscription(user_id: str, sub_id: str) -> bool:
        """
        Permanently deletes subscription from Supabase database and purges corresponding Google Calendar event.
        Guarantees all duplicate/ghost rows matching the ID or merchant name for this user are purged safely.
        """
        clean_uid = str(user_id).strip('"\'')
        clean_sid = str(sub_id).strip('"\'')

        existing = SubscriptionService.get_subscription_by_id(clean_uid, clean_sid)
        merchant = existing.get("merchant_name") if existing else None
        actual_id = existing.get("id") if existing else clean_sid
        cal_id = existing.get("calendar_event_id") if existing else None

        supabase = get_supabase_client()

        # 1. Direct DB Deletion by exact ID from Supabase
        try:
            supabase.from_("subscriptions").delete().eq("id", str(actual_id)).eq("user_id", clean_uid).execute()
        except Exception as err:
            print("Supabase REST delete error:", err)

        if str(actual_id) != str(clean_sid):
            try:
                supabase.from_("subscriptions").delete().eq("id", str(clean_sid)).eq("user_id", clean_uid).execute()
            except Exception:
                pass

        # 2. Safely purge any duplicate rows matching the merchant name for this user by exact ID
        if merchant:
            try:
                m_clean = merchant.strip().lower()
                all_user_subs = supabase.from_("subscriptions").select("id, merchant_name").eq("user_id", clean_uid).execute()
                if all_user_subs.data:
                    for item in all_user_subs.data:
                        item_m = str(item.get("merchant_name") or "").strip().lower()
                        if item_m == m_clean and str(item.get("id")) != str(actual_id):
                            supabase.from_("subscriptions").delete().eq("id", str(item.get("id"))).eq("user_id", clean_uid).execute()
            except Exception as e_m:
                print("Supabase REST duplicate cleanup note:", e_m)

        # 3. Fast Calendar Agent delete sync
        try:
            from app.services.calendar_agent_service import CalendarAgentService
            CalendarAgentService.sync_subscription_delete(
                user_id=clean_uid,
                sub_id=str(actual_id),
                merchant_name=merchant,
                calendar_event_id=cal_id
            )
        except Exception as cal_err:
            print("Calendar Agent trigger error on delete_subscription:", cal_err)

        return True

    @staticmethod
    def calculate_rolled_over_date(current_date_str: str, billing_frequency: str = "monthly", target_today=None) -> str:
        """
        Calendar-aware rollover calculation. Repeatedly advances the date until new_date >= today.
        Supports monthly, yearly, weekly, daily, and quarterly frequencies.
        """
        from datetime import date, timedelta, datetime
        if not target_today:
            target_today = date.today()

        try:
            curr = datetime.strptime(str(current_date_str)[:10], "%Y-%m-%d").date()
        except Exception:
            return str(target_today)

        freq = (billing_frequency or "monthly").strip().lower()

        # If already strictly in the future, return as is
        if curr > target_today:
            return str(curr)

        # Loop until current date is strictly ahead of target_today
        max_loops = 1000  # safety circuit breaker
        loops = 0
        while curr <= target_today and loops < max_loops:
            loops += 1
            if freq == "yearly" or freq == "annual":
                try:
                    curr = curr.replace(year=curr.year + 1)
                except ValueError:
                    curr = curr + timedelta(days=365)
            elif freq == "weekly":
                curr = curr + timedelta(days=7)
            elif freq == "daily":
                curr = curr + timedelta(days=1)
            elif freq == "quarterly":
                month = curr.month + 3
                year = curr.year + (month - 1) // 12
                month = (month - 1) % 12 + 1
                days_in_month = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
                day = min(curr.day, days_in_month)
                curr = date(year, month, day)
            else:  # monthly default
                month = curr.month + 1
                year = curr.year + (month - 1) // 12
                month = (month - 1) % 12 + 1
                days_in_month = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
                day = min(curr.day, days_in_month)
                curr = date(year, month, day)

        return str(curr)

    @staticmethod
    def auto_rollover_overdue_subscriptions(user_id: Optional[str] = None, sync_calendar: bool = True) -> List[dict]:
        """
        Scans subscriptions for overdue next_payment_dates (next_payment_date < today) or expired trials,
        rolls them forward to the next cycle date, updates Supabase DB, and optionally updates Google Calendar.
        """
        from datetime import date, datetime

        today = date.today()
        supabase = get_supabase_client()

        query = supabase.from_("subscriptions").select("*")
        if user_id:
            clean_uid = str(user_id).strip('"\'')
            query = query.eq("user_id", clean_uid)

        try:
            res = query.execute()
            all_subs = res.data or []
        except Exception as e:
            print("auto_rollover_overdue_subscriptions fetch error:", e)
            all_subs = []

        updated_list = []
        for sub in all_subs:
            status = str(sub.get("status") or "active").lower()
            if status == "cancelled":
                continue

            sub_id = str(sub.get("id"))
            sub_uid = str(sub.get("user_id"))
            next_pay_str = sub.get("next_payment_date")
            is_trial = status == "trial" or sub.get("is_free_trial")
            freq = sub.get("billing_frequency") or "monthly"
            trial_end = sub.get("trial_end_date")

            is_overdue = False
            if next_pay_str:
                try:
                    next_pay_date = datetime.strptime(str(next_pay_str)[:10], "%Y-%m-%d").date()
                    if next_pay_date < today:
                        is_overdue = True
                except Exception:
                    pass

            trial_expired = False
            if is_trial:
                trial_end_val = trial_end or next_pay_str
                if trial_end_val:
                    try:
                        trial_end_date_obj = datetime.strptime(str(trial_end_val)[:10], "%Y-%m-%d").date()
                        if trial_end_date_obj <= today:
                            trial_expired = True
                    except Exception:
                        pass

            if is_overdue or trial_expired:
                # Calculate rolled forward date
                base_date = next_pay_str
                if trial_expired and sub.get("expected_first_payment_date"):
                    base_date = sub.get("expected_first_payment_date")

                new_next_date = SubscriptionService.calculate_rolled_over_date(
                    base_date or str(today), freq, target_today=today
                )

                update_payload = {
                    "next_payment_date": new_next_date
                }
                if is_trial and trial_expired:
                    update_payload["status"] = "active"
                    update_payload["is_free_trial"] = False

                # Persist to database
                try:
                    up_res = supabase.from_("subscriptions").update(update_payload).eq("id", sub_id).execute()
                    if up_res.data and len(up_res.data) > 0:
                        merged = {**sub, **up_res.data[0], **update_payload}
                    else:
                        sub.update(update_payload)
                        merged = sub
                except Exception:
                    # Fallback update core keys
                    try:
                        fallback_payload = {"next_payment_date": new_next_date}
                        if is_trial and trial_expired:
                            fallback_payload["status"] = "active"
                        up_res2 = supabase.from_("subscriptions").update(fallback_payload).eq("id", sub_id).execute()
                        if up_res2.data and len(up_res2.data) > 0:
                            merged = {**sub, **up_res2.data[0], **fallback_payload}
                        else:
                            sub.update(fallback_payload)
                            merged = sub
                    except Exception:
                        sub.update(update_payload)
                        merged = sub

                # In-place Google Calendar sync (only when sync_calendar is True, e.g. scheduled background jobs)
                if sync_calendar:
                    try:
                        from app.services.calendar_agent_service import CalendarAgentService
                        cal_res = CalendarAgentService.sync_subscription_update(sub_uid, merged)
                        if cal_res and "calendar_event_id" in cal_res:
                            merged["calendar_event_id"] = cal_res["calendar_event_id"]
                        print(f"🔁 Auto-rolled Subscription '{merged.get('merchant_name')}' to {new_next_date}. Calendar synced.")
                    except Exception as cal_err:
                        print(f"Calendar sync error during rollover for sub {sub_id}:", cal_err)

                updated_list.append(merged)

        return updated_list

    @staticmethod
    def process_trial_conversions(user_id: Optional[str] = None) -> List[dict]:
        """
        Alias / wrapper for trial conversions and date rollovers.
        """
        return SubscriptionService.auto_rollover_overdue_subscriptions(user_id)





