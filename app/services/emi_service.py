import uuid
from typing import List, Optional
from datetime import datetime, timedelta, date
from app.schemas.emi import EMICreate, EMIUpdate
from app.core.security import get_supabase_client


def calculate_completion_percentage(paid: int, total: int) -> float:
    if not total or total <= 0:
        return 0.0
    return round((min(paid, total) / total) * 100.0, 2)


class EMIService:
    @staticmethod
    def create_emi(user_id: str, payload: EMICreate, trigger_calendar: bool = True) -> dict:
        emi_id = str(uuid.uuid4())
        clean_uid = str(user_id).strip('"\'')
        total_inst = payload.total_installments
        paid_inst = payload.installments_paid or 0
        inst_amt = float(payload.installment_amount)
        
        # Calculate remaining amount if not provided
        rem_amt = payload.remaining_amount
        if rem_amt is None:
            rem_amt = max(0.0, (total_inst - paid_inst) * inst_amt)

        pct = calculate_completion_percentage(paid_inst, total_inst)
        status_val = payload.status or "active"
        if paid_inst >= total_inst:
            status_val = "completed"
            rem_amt = 0.0

        new_data = {
            "id": emi_id,
            "user_id": clean_uid,
            "loan_name": payload.loan_name,
            "total_installments": total_inst,
            "installments_paid": paid_inst,
            "installment_amount": inst_amt,
            "start_date": str(payload.start_date) if payload.start_date else None,
            "next_due_date": str(payload.next_due_date),
            "remaining_amount": float(rem_amt),
            "status": status_val,
            "completion_percentage": pct
        }

        created_emi = new_data
        supabase = get_supabase_client()
        try:
            insert_payload = {k: v for k, v in new_data.items() if k != "completion_percentage"}
            existing = supabase.from_("emis").select("id").eq("user_id", clean_uid).ilike("loan_name", payload.loan_name.strip()).execute()
            if existing.data and len(existing.data) > 0:
                existing_id = existing.data[0]["id"]
                insert_payload["id"] = existing_id
                up_res = supabase.from_("emis").update(insert_payload).eq("id", existing_id).execute()
                if up_res.data and len(up_res.data) > 0:
                    res_data = up_res.data[0]
                    res_data["completion_percentage"] = pct
                    created_emi = res_data
            else:
                res = supabase.from_("emis").insert(insert_payload).execute()
                if res.data and len(res.data) > 0:
                    res_data = res.data[0]
                    res_data["completion_percentage"] = pct
                    created_emi = res_data
        except Exception as err:
            print("Supabase REST EMI insert/upsert error:", err)

        # Trigger Automatic Calendar Agent for EMI if requested
        if trigger_calendar:
            try:
                from app.services.calendar_agent_service import CalendarAgentService
                cal_res = CalendarAgentService.handle_command({
                    "action": "CREATE_CALENDAR_EVENT",
                    "type": "EMI",
                    "user_id": clean_uid,
                    "payload": created_emi
                })
                if cal_res:
                    created_emi["calendar_event_id"] = cal_res.get("calendar_event_id")
                    created_emi["calendar_sync_status"] = cal_res.get("calendar_sync_status", "PENDING")
                    created_emi["calendar_sync_error"] = cal_res.get("calendar_sync_error")
            except Exception as cal_err:
                print("Calendar Agent trigger error on create_emi:", cal_err)
                created_emi["calendar_sync_status"] = "FAILED"
                created_emi["calendar_sync_error"] = str(cal_err)

        return created_emi

    @staticmethod
    def seed_initial_mock_emis(user_id: str) -> List[dict]:
        """
        Seeds initial mock EMI loans for a new user directly into Supabase PostgreSQL.
        """
        from datetime import date, timedelta
        today = date.today()
        clean_uid = str(user_id).strip('"\'')

        default_emis = [
            {"loan_name": "education loan", "total_installments": 12, "installments_paid": 0, "installment_amount": 4500.0, "next_due_date": str(today + timedelta(days=13)), "status": "active"},
            {"loan_name": "iPhone 15 Pro EMI", "total_installments": 12, "installments_paid": 4, "installment_amount": 4500.0, "next_due_date": str(today + timedelta(days=19)), "status": "active"},
            {"loan_name": "HDFC Home Appliance Loan", "total_installments": 6, "installments_paid": 5, "installment_amount": 2200.0, "next_due_date": str(today + timedelta(days=12)), "status": "active"}
        ]

        created = []
        for item in default_emis:
            try:
                emi_data = EMIService.create_emi(user_id=clean_uid, payload=EMICreate(**item), trigger_calendar=False)
                created.append(emi_data)
            except Exception as e:
                print("Error seeding mock EMI item:", e)

        return created

    @staticmethod
    def get_user_emis(user_id: str) -> List[dict]:
        clean_uid = str(user_id).strip('"\'')
        raw_emis = []
        supabase = get_supabase_client()
        try:
            res = supabase.from_("emis").select("*").eq("user_id", clean_uid).execute()
            if res.data and len(res.data) > 0:
                raw_emis = res.data
        except Exception as err:
            print("Supabase REST EMI select error:", err)

        # FAST PATH: Only check mock init if no EMIs exist (skip 3 extra DB queries)
        if not raw_emis:
            from app.services.mock_generator_service import MockGeneratorService
            if not MockGeneratorService.is_mock_data_initialized(clean_uid):
                MockGeneratorService.ensure_one_time_mock_initialization(clean_uid)
                try:
                    res = supabase.from_("emis").select("*").eq("user_id", clean_uid).execute()
                    if res.data:
                        raw_emis = res.data
                except Exception as err:
                    print("Supabase REST EMI re-select after initialization error:", err)

        # Deduplicate by loan_name
        unique_emis = []
        seen_loans = set()
        for item in raw_emis:
            item["completion_percentage"] = calculate_completion_percentage(
                item.get("installments_paid", 0), item.get("total_installments", 1)
            )
            name_key = (item.get("loan_name") or "").strip().lower()
            if name_key:
                if name_key in seen_loans:
                    continue
                seen_loans.add(name_key)
            unique_emis.append(item)

        return unique_emis

    @staticmethod
    def get_emi_by_id(user_id: str, emi_id: str) -> Optional[dict]:
        clean_uid = str(user_id).strip('"\'')
        clean_eid = str(emi_id).strip('"\'')

        supabase = get_supabase_client()
        try:
            res = supabase.from_("emis").select("*").eq("id", clean_eid).eq("user_id", clean_uid).execute()
            if res.data and len(res.data) > 0:
                data = res.data[0]
                data["completion_percentage"] = calculate_completion_percentage(
                    data.get("installments_paid", 0), data.get("total_installments", 1)
                )
                return data
        except Exception as err:
            pass

        try:
            res = supabase.from_("emis").select("*").eq("user_id", clean_uid).execute()
            if res.data:
                for e in res.data:
                    e_id = str(e.get("id")).strip('"\'')
                    l_name = str(e.get("loan_name") or e.get("lender_name") or "").strip().lower()
                    if e_id == clean_eid or clean_eid.lower() in l_name or l_name in clean_eid.lower():
                        e["completion_percentage"] = calculate_completion_percentage(
                            e.get("installments_paid", 0), e.get("total_installments", 1)
                        )
                        return e
        except Exception as err:
            pass

        return None

    @staticmethod
    def update_emi(user_id: str, emi_id: str, payload: EMIUpdate) -> Optional[dict]:
        clean_uid = str(user_id).strip('"\'')
        clean_eid = str(emi_id).strip('"\'')
        existing = EMIService.get_emi_by_id(clean_uid, clean_eid)
        if not existing:
            loan_fallback = clean_eid.replace("emi-", "").replace("-", " ")
            existing = {
                "id": clean_eid,
                "user_id": clean_uid,
                "loan_name": loan_fallback,
                "total_installments": 12,
                "installments_paid": 0,
                "installment_amount": 0.0,
                "status": "active"
            }

        update_data = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None and k != "pay_installment"}

        # Auto-handle Pay Installment action
        if payload.pay_installment:
            current_paid = existing.get("installments_paid", 0) + 1
            total_inst = update_data.get("total_installments", existing.get("total_installments", 1))
            inst_amt = float(update_data.get("installment_amount", existing.get("installment_amount", 0)))
            curr_rem = float(existing.get("remaining_amount", total_inst * inst_amt))

            update_data["installments_paid"] = current_paid
            update_data["remaining_amount"] = max(0.0, curr_rem - inst_amt)

            # Advance next_due_date by 30 days
            try:
                curr_date = datetime.strptime(str(existing.get("next_due_date")), "%Y-%m-%d")
                new_date = curr_date + timedelta(days=30)
                update_data["next_due_date"] = new_date.strftime("%Y-%m-%d")
            except Exception:
                pass

            if current_paid >= total_inst:
                update_data["status"] = "completed"
                update_data["remaining_amount"] = 0.0

        if "start_date" in update_data and update_data["start_date"]:
            update_data["start_date"] = str(update_data["start_date"])
        if "next_due_date" in update_data and update_data["next_due_date"]:
            update_data["next_due_date"] = str(update_data["next_due_date"])

        existing.update(update_data)
        existing["completion_percentage"] = calculate_completion_percentage(
            existing.get("installments_paid", 0), existing.get("total_installments", 1)
        )

        supabase = get_supabase_client()
        updated_emi = existing
        try:
            db_update_payload = {k: v for k, v in update_data.items() if k != "completion_percentage"}
            res = supabase.from_("emis").update(db_update_payload).eq("id", clean_eid).eq("user_id", clean_uid).execute()
            if res.data and len(res.data) > 0:
                data = res.data[0]
                data["completion_percentage"] = calculate_completion_percentage(
                    data.get("installments_paid", 0), data.get("total_installments", 1)
                )
                updated_emi = data
        except Exception as err:
            print("Supabase REST EMI update error:", err)

        if updated_emi:
            try:
                from app.services.calendar_agent_service import CalendarAgentService
                if updated_emi.get("status") in ["cancelled", "paid"] or updated_emi.get("autopay_enabled") == False:
                    cal_res = CalendarAgentService.sync_emi_delete(
                        user_id=clean_uid,
                        emi_id=clean_eid,
                        loan_name=updated_emi.get("loan_name"),
                        calendar_event_id=updated_emi.get("calendar_event_id")
                    )
                    updated_emi["calendar_event_id"] = None
                else:
                    cal_res = CalendarAgentService.sync_emi_update(
                        user_id=clean_uid,
                        emi=updated_emi
                    )
                    if cal_res and "calendar_event_id" in cal_res:
                        updated_emi["calendar_event_id"] = cal_res["calendar_event_id"]
            except Exception as cal_err:
                print("Calendar Agent trigger error on update_emi:", cal_err)

        return updated_emi

    @staticmethod
    def soft_delete_emi(user_id: str, emi_id: str) -> Optional[dict]:
        return EMIService.update_emi(user_id, emi_id, EMIUpdate(status="cancelled"))

    @staticmethod
    def delete_emi(user_id: str, emi_id: str) -> bool:
        """
        Permanently deletes EMI record from Supabase database and purges corresponding Google Calendar event.
        Guarantees all duplicate/ghost rows matching the ID or loan name for this user are purged.
        """
        clean_uid = str(user_id).strip('"\'')
        clean_eid = str(emi_id).strip('"\'')

        existing = EMIService.get_emi_by_id(clean_uid, clean_eid)
        loan_name = existing.get("loan_name") if existing else None
        actual_id = existing.get("id") if existing else clean_eid
        cal_id = existing.get("calendar_event_id") if existing else None

        supabase = get_supabase_client()
        try:
            supabase.from_("emis").delete().eq("id", str(actual_id)).eq("user_id", clean_uid).execute()
        except Exception as err:
            print("Supabase REST EMI delete error:", err)

        if str(actual_id) != str(clean_eid):
            try:
                supabase.from_("emis").delete().eq("id", str(clean_eid)).eq("user_id", clean_uid).execute()
            except Exception:
                pass

        if loan_name:
            try:
                supabase.from_("emis").delete().ilike("loan_name", loan_name.strip()).eq("user_id", clean_uid).execute()
            except Exception as e_l:
                print("Supabase REST EMI delete by loan_name note:", e_l)

        try:
            from app.services.calendar_agent_service import CalendarAgentService
            CalendarAgentService.sync_emi_delete(
                user_id=clean_uid,
                emi_id=str(actual_id),
                loan_name=loan_name,
                calendar_event_id=cal_id
            )
        except Exception as cal_err:
            print("Calendar Agent trigger error on delete_emi:", cal_err)

        return True

    @staticmethod
    def calculate_rolled_over_due_date(current_date_str: str, target_today=None) -> str:
        """
        Calendar-aware rollover calculation for EMI due dates (monthly standard).
        Advances by months until new_date >= today.
        """
        from datetime import date, timedelta
        if not target_today:
            target_today = date.today()

        try:
            curr = datetime.strptime(str(current_date_str)[:10], "%Y-%m-%d").date()
        except Exception:
            return str(target_today)

        if curr >= target_today:
            return str(curr)

        max_loops = 1000
        loops = 0
        while curr < target_today and loops < max_loops:
            loops += 1
            month = curr.month + 1
            year = curr.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            days_in_month = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
            day = min(curr.day, days_in_month)
            curr = date(year, month, day)

        return str(curr)

    @staticmethod
    def auto_rollover_overdue_emis(user_id: Optional[str] = None, sync_calendar: bool = True) -> List[dict]:
        """
        Scans EMIs for overdue next_due_dates (next_due_date < today),
        rolls them forward to the next cycle date, updates Supabase DB, and optionally updates Google Calendar.
        """
        today = date.today()
        supabase = get_supabase_client()

        query = supabase.from_("emis").select("*")
        if user_id:
            clean_uid = str(user_id).strip('"\'')
            query = query.eq("user_id", clean_uid)

        try:
            res = query.execute()
            all_emis = res.data or []
        except Exception as e:
            print("auto_rollover_overdue_emis fetch error:", e)
            all_emis = []

        updated_list = []
        for emi in all_emis:
            status = str(emi.get("status") or "active").lower()
            if status in ["cancelled", "completed", "paid"]:
                continue

            emi_id = str(emi.get("id"))
            emi_uid = str(emi.get("user_id"))
            next_due_str = emi.get("next_due_date")

            is_overdue = False
            if next_due_str:
                try:
                    next_due_date = datetime.strptime(str(next_due_str)[:10], "%Y-%m-%d").date()
                    if next_due_date < today:
                        is_overdue = True
                except Exception:
                    pass

            if is_overdue:
                new_next_date = EMIService.calculate_rolled_over_due_date(
                    next_due_str or str(today), target_today=today
                )

                update_payload = {
                    "next_due_date": new_next_date
                }

                try:
                    up_res = supabase.from_("emis").update(update_payload).eq("id", emi_id).execute()
                    if up_res.data and len(up_res.data) > 0:
                        merged = {**emi, **up_res.data[0], **update_payload}
                    else:
                        emi.update(update_payload)
                        merged = emi
                except Exception as err:
                    print(f"Error persisting rollover for EMI {emi_id}:", err)
                    emi.update(update_payload)
                    merged = emi

                # Update completion percentage
                merged["completion_percentage"] = calculate_completion_percentage(
                    merged.get("installments_paid", 0), merged.get("total_installments", 1)
                )

                # In-place Google Calendar sync (only when sync_calendar is True)
                if sync_calendar:
                    try:
                        from app.services.calendar_agent_service import CalendarAgentService
                        cal_res = CalendarAgentService.sync_emi_update(emi_uid, merged)
                        if cal_res and "calendar_event_id" in cal_res:
                            merged["calendar_event_id"] = cal_res["calendar_event_id"]
                        print(f"🔁 Auto-rolled EMI '{merged.get('loan_name')}' to {new_next_date}. Calendar synced.")
                    except Exception as cal_err:
                        print(f"Calendar sync error during rollover for EMI {emi_id}:", cal_err)

                updated_list.append(merged)

        return updated_list



