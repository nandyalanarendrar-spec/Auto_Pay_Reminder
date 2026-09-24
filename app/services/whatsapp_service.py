import re
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional
from app.core.config import settings

# =====================================================================
# 📱 META WHATSAPP CLOUD API INTEGRATION SERVICE
# =====================================================================

class WhatsAppService:

    @staticmethod
    def _clean_phone_number(phone: str) -> str:
        """
        Sanitizes raw phone number to international E.164 format without '+' or spaces.
        Example: '+91 98765 43210' -> '919876543210'
        """
        digits = re.sub(r"\D", "", str(phone or ""))
        if not digits:
            return "919876543210" # Default fallback
        # If 10 digits (e.g. Indian mobile number without country code), prepend '91'
        if len(digits) == 10:
            digits = "91" + digits
        return digits

    @classmethod
    def send_whatsapp_message(cls, to_phone: str, text_body: str) -> Dict[str, Any]:
        """
        Dispatches a WhatsApp text message via Meta Graph API (WhatsApp Cloud API v18.0).
        If Meta API credentials are not set in .env, operates in Simulation/Demo Mode.
        """
        phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "") or ""
        access_token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "") or ""
        target_phone = cls._clean_phone_number(to_phone)

        # 1. Check if Meta WhatsApp Cloud API credentials are configured
        if not phone_number_id or not access_token:
            print(f"📱 [WhatsApp SIMULATOR] Outgoing alert to +{target_phone}:")
            print(f"--------------------------------------------------")
            print(text_body)
            print(f"--------------------------------------------------")
            return {
                "status": "simulated",
                "message": "WhatsApp message simulated (Configure WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN in .env for live Meta delivery).",
                "recipient": target_phone,
                "body": text_body
            }

        # 2. Live Meta WhatsApp Cloud API HTTP POST Request
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": target_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text_body
            }
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")

            with urllib.request.urlopen(req) as resp:
                res_body = json.loads(resp.read().decode("utf-8"))
                msg_id = res_body.get("messages", [{}])[0].get("id", "N/A")
                print(f"✅ [WhatsApp Live Sent] Message delivered to +{target_phone} (Meta WAMID: {msg_id})")
                return {
                    "status": "success",
                    "whatsapp_message_id": msg_id,
                    "recipient": target_phone,
                    "meta_response": res_body
                }
        except Exception as err:
            print(f"❌ [WhatsApp Meta Cloud API Error] Failed to send to +{target_phone}:", err)
            return {
                "status": "error",
                "error": str(err),
                "recipient": target_phone
            }

    @classmethod
    def send_payment_reminder(
        cls,
        to_phone: str,
        user_name: str,
        item_name: str,
        amount: float,
        due_date: str,
        days_left: int,
        is_trial: bool = False
    ) -> Dict[str, Any]:
        """
        Formats and dispatches an urgent payment/trial reminder alert via WhatsApp.
        """
        greeting = f"Hello {user_name}!" if user_name else "Hello!"
        days_str = "TODAY" if days_left == 0 else (f"tomorrow (in 1 day)" if days_left == 1 else f"in {days_left} days")

        if is_trial:
            body = (
                f"🛑 *Autopay Guard Trial Expiry Alert*\n\n"
                f"{greeting}\n"
                f"Your free trial for *{item_name}* is expiring *{days_str}* on *{due_date}*!\n\n"
                f"• *Amount after trial*: ₹{amount:,.2f}/month\n"
                f"• *Action Required*: Revoke your UPI mandate 24 hours before charge date to prevent auto-debit.\n\n"
                f"🛡️ *Autopay Guard Safety Protection*"
            )
        else:
            body = (
                f"⚡ *Autopay Guard Payment Due Alert*\n\n"
                f"{greeting}\n"
                f"Your recurring subscription *{item_name}* of *₹{amount:,.2f}* is due *{days_str}* on *{due_date}*.\n\n"
                f"Please ensure your linked bank account or UPI has sufficient balance to avoid payment failure or bank penalty fees.\n\n"
                f"🛡️ *Autopay Guard Automated Assistant*"
            )

        return cls.send_whatsapp_message(to_phone=to_phone, text_body=body)

    @classmethod
    def send_test_message(cls, to_phone: str, user_name: str = "Narendra") -> Dict[str, Any]:
        """
        Dispatches an instant test message to verify WhatsApp integration.
        """
        body = (
            f"✅ *Autopay Guard WhatsApp Integration Active*\n\n"
            f"Hello {user_name}! Your Meta WhatsApp Cloud API messaging is connected.\n\n"
            f"You will receive instant alerts for upcoming subscriptions, trial expirations, and EMI auto-debits directly on WhatsApp!\n\n"
            f"🛡️ *Autopay Guard Automated System*"
        )
        return cls.send_whatsapp_message(to_phone=to_phone, text_body=body)
