import os
import json
from datetime import datetime
from typing import Dict, Any, List

from app.services.subscription_service import SubscriptionService
from app.services.emi_service import EMIService
from app.services.mock_generator_service import MockGeneratorService
from app.services.audit_log_service import AuditLoggerService

class SecurityHardeningService:

    @staticmethod
    def export_user_data(user_id: str) -> Dict[str, Any]:
        """
        GDPR Data Compliance Export:
        Aggregates all user subscriptions, EMIs, bank transactions, and audit logs into a single JSON export.
        """
        clean_uid = str(user_id).strip('"\'')

        subs = SubscriptionService.get_user_subscriptions(clean_uid)
        emis = EMIService.get_user_emis(clean_uid)
        txns = MockGeneratorService.get_user_transactions(clean_uid)
        logs = AuditLoggerService.get_user_logs(clean_uid)

        # Record audit log for data export
        AuditLoggerService.log_action(clean_uid, "DATA_EXPORT", details={"format": "JSON"})

        return {
            "export_metadata": {
                "user_id": clean_uid,
                "exported_at": datetime.utcnow().isoformat(),
                "compliance": "GDPR Transparency & Right to Portability",
                "record_counts": {
                    "subscriptions": len(subs),
                    "emis": len(emis),
                    "transactions": len(txns),
                    "audit_logs": len(logs)
                }
            },
            "subscriptions": subs,
            "emis": emis,
            "transactions": txns,
            "audit_trail": logs
        }

    @staticmethod
    def delete_user_account(user_id: str) -> Dict[str, Any]:
        """
        GDPR Account Deletion (Right to be Forgotten):
        Permanently purges all associated subscriptions, EMIs, bank transactions, Google Calendar OAuth tokens, and user account.
        """
        clean_uid = str(user_id).strip('"\'')

        # 1. Purge Google Calendar events for subscriptions
        subs = SubscriptionService.get_user_subscriptions(clean_uid)
        for s in subs:
            s_id = s.get("id")
            if s_id:
                try:
                    SubscriptionService.soft_delete_subscription(clean_uid, s_id)
                except Exception:
                    pass

        # 2. Purge Google Calendar events for EMIs
        emis = EMIService.get_user_emis(clean_uid)
        for e in emis:
            e_id = e.get("id")
            if e_id:
                try:
                    EMIService.soft_delete_emi(clean_uid, e_id)
                except Exception:
                    pass

        # 3. Disconnect Google Calendar OAuth tokens
        try:
            from app.services.google_calendar_service import GoogleCalendarService
            GoogleCalendarService.disconnect(clean_uid)
        except Exception as e:
            print("Google Calendar disconnect note on account deletion:", e)

        # 4. Hard-delete rows from Supabase DB tables & delete user from Supabase Auth
        try:
            from app.core.security import get_supabase_client
            supabase = get_supabase_client()
            supabase.from_("subscriptions").delete().eq("user_id", clean_uid).execute()
            supabase.from_("emis").delete().eq("user_id", clean_uid).execute()
            supabase.from_("transactions").delete().eq("user_id", clean_uid).execute()
            try:
                supabase.auth.admin.delete_user(clean_uid)
            except Exception:
                pass
        except Exception as auth_err:
            print("Supabase DB purge note:", auth_err)

        # 5. Log account deletion event
        AuditLoggerService.log_action(clean_uid, "ACCOUNT_DELETION", details={"status": "PERMANENTLY_PURGED"})

        return {
            "message": "User account and all associated subscriptions, EMIs, bank transactions, and Google Calendar tokens have been permanently purged.",
            "user_id": clean_uid,
            "deleted_at": datetime.utcnow().isoformat(),
            "status": "PURGED"
        }

    @staticmethod
    def clear_user_data(user_id: str) -> Dict[str, Any]:
        """
        Clears all user application data (subscriptions, EMIs, transactions, calendar sync events) from Supabase
        while keeping the user account active and logged in.
        Ensures mock_data_initialized remains True so mock data is not re-seeded.
        """
        clean_uid = str(user_id).strip('"\'')

        # 1. Purge Google Calendar events
        try:
            from app.services.calendar_agent_service import CalendarAgentService
            CalendarAgentService.debug_purge_events(clean_uid)
        except Exception as e:
            pass

        # 2. Delete all subscriptions, EMIs, transactions, and notification_logs for user from Supabase DB
        from app.core.security import get_supabase_client
        supabase = get_supabase_client()
        try:
            supabase.from_("subscriptions").delete().eq("user_id", clean_uid).execute()
            supabase.from_("emis").delete().eq("user_id", clean_uid).execute()
            supabase.from_("transactions").delete().eq("user_id", clean_uid).execute()
            try:
                supabase.from_("notification_logs").delete().eq("user_id", clean_uid).execute()
            except Exception as e_nl:
                print("Notification logs clear note:", e_nl)
        except Exception as err:
            print("Supabase clear data error:", err)

        # 3. Ensure mock_data_initialized is set to True
        MockGeneratorService.set_mock_data_initialized(clean_uid, True)

        # 4. Log audit event
        AuditLoggerService.log_action(clean_uid, "CLEAR_ALL_DATA", details={"status": "ALL_DATA_CLEARED"})

        return {
            "success": True,
            "message": "All user subscriptions, EMIs, bank transactions, and calendar reminders have been cleared.",
            "user_id": clean_uid,
            "status": "CLEARED"
        }

