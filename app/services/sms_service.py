import os
import re
import requests
import logging
from typing import Dict, Any

logger = logging.getLogger("autopay.sms")

FAST2SMS_URL = "https://www.fast2sms.com/dev/bulkV2"

def validate_and_clean_indian_phone(phone_number: str) -> str:
    """
    Cleans and validates 10-digit Indian mobile numbers.
    Strips +91, 91 prefix, spaces, and non-digit characters.
    Returns cleaned 10-digit string or raises ValueError.
    """
    if not phone_number:
        raise ValueError("Phone number cannot be empty.")

    # Remove all non-digit characters
    cleaned = re.sub(r"\D", "", str(phone_number))

    # Strip 91 prefix if 12 digits (e.g., 919876543210 -> 9876543210)
    if len(cleaned) == 12 and cleaned.startswith("91"):
        cleaned = cleaned[2:]
    elif len(cleaned) == 11 and cleaned.startswith("0"):
        cleaned = cleaned[1:]

    if len(cleaned) != 10 or not cleaned.isdigit():
        raise ValueError(f"Invalid Indian mobile number '{phone_number}'. Must be exactly 10 digits.")

    return cleaned


def send_sms(phone_number: str, message: str) -> Dict[str, Any]:
    """
    Sends Quick SMS via Fast2SMS API route 'q'.
    Does not require TRAI DLT template registration for dev testing.
    """
    api_key = os.getenv("FAST2SMS_API_KEY")
    if not api_key:
        logger.error("FAST2SMS_API_KEY is not configured in environment variables.")
        return {
            "success": False,
            "error": "FAST2SMS_API_KEY environment variable is missing."
        }

    # 1. Validate phone number
    try:
        clean_phone = validate_and_clean_indian_phone(phone_number)
    except ValueError as ve:
        logger.warning(f"SMS phone validation failed: {ve}")
        return {
            "success": False,
            "error": str(ve)
        }

    # 2. Build Fast2SMS API Request
    headers = {
        "authorization": api_key.strip(),
        "Content-Type": "application/json"
    }

    payload = {
        "route": "q",
        "message": message,
        "language": "english",
        "numbers": clean_phone
    }

    try:
        response = requests.post(FAST2SMS_URL, json=payload, headers=headers, timeout=10)
        res_json = response.json()
        
        is_success = response.status_code == 200 and res_json.get("return") is True

        return {
            "success": is_success,
            "status_code": response.status_code,
            "response": res_json
        }

    except Exception as err:
        logger.error(f"Fast2SMS API HTTP request failed: {err}")
        return {
            "success": False,
            "error": f"Fast2SMS request exception: {str(err)}"
        }
