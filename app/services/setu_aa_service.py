import base64
import json
import re
import threading
import time
from typing import Any, Dict, Optional

import requests

from app.core.config import settings

TIMEOUT_SECONDS = 30
USER_AGENT = "Mozilla/5.0 (compatible; AutopayGuard/1.0; +https://auto-pay-reminder.vercel.app)"


class SetuError(Exception):
    def __init__(self, message: str, status: Optional[int] = None):
        super().__init__(message)
        self.status = status


def _clean(value: Any) -> str:
    # A stray newline pasted with a credential made Setu reject the login before; always trim.
    return str(value or "").strip()


def is_configured() -> bool:
    return all(_clean(v) for v in (
        settings.SETU_CLIENT_ID, settings.SETU_CLIENT_SECRET,
        settings.SETU_PRODUCT_INSTANCE_ID, settings.SETU_BASE_URL,
    ))


_token_lock = threading.Lock()
_token_cache: Dict[str, Any] = {"value": None, "expires_at": 0.0}


def _jwt_expiry(token: str) -> float:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return float(json.loads(base64.urlsafe_b64decode(payload)).get("exp", 0))
    except Exception:
        return time.time() + 600


def _error_text(response: requests.Response) -> str:
    try:
        data = response.json()
        return str(data.get("errorMsg") or data.get("message") or data.get("errorCode") or data)[:300]
    except Exception:
        # Not Setu's normal JSON error - usually a firewall/CDN page. Say who answered and what it said.
        plain = re.sub(r"<[^>]+>", " ", response.text or "")
        plain = re.sub(r"\s+", " ", plain).strip()[:140]
        server = response.headers.get("server") or response.headers.get("via") or "unknown"
        return f"HTTP {response.status_code} from {server}: {plain or 'empty response'}"


class _RelayResponse:
    """The parts of requests.Response this module uses, rebuilt from the relay's JSON reply."""

    def __init__(self, data: Dict[str, Any]):
        self.status_code = int(data.get("status") or 0)
        self.text = data.get("body") or ""
        self.headers = {"server": data.get("server") or "", "content-type": data.get("content_type") or ""}

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    def json(self) -> Any:
        return json.loads(self.text)


def _send(method: str, url: str, headers: Dict[str, str], body: Optional[dict] = None):
    """Call Setu directly, or through the Indian-region relay when SETU_RELAY_URL is set."""
    relay_url = _clean(settings.SETU_RELAY_URL)
    if not relay_url:
        return requests.request(method, url, json=body, headers=headers, timeout=TIMEOUT_SECONDS)

    res = requests.post(
        relay_url,
        json={"method": method, "url": url, "headers": headers, "body": body},
        headers={"x-relay-key": _clean(settings.SETU_RELAY_KEY), "Content-Type": "application/json"},
        timeout=TIMEOUT_SECONDS + 5,
    )
    if res.status_code != 200:
        raise SetuError(f"Setu relay refused the request (HTTP {res.status_code}). Check SETU_RELAY_URL / SETU_RELAY_KEY.", 502)
    try:
        return _RelayResponse(res.json())
    except ValueError:
        raise SetuError("Setu relay returned an unreadable reply.", 502)


def _get_token(force: bool = False) -> str:
    with _token_lock:
        if not force and _token_cache["value"] and _token_cache["expires_at"] - 60 > time.time():
            return _token_cache["value"]
        try:
            res = _send(
                "POST",
                _clean(settings.SETU_AUTH_URL),
                {
                    "x-product-instance-id": _clean(settings.SETU_PRODUCT_INSTANCE_ID),
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                {
                    "clientID": _clean(settings.SETU_CLIENT_ID),
                    "grant_type": "client_credentials",
                    "secret": _clean(settings.SETU_CLIENT_SECRET),
                },
            )
        except requests.RequestException as err:
            raise SetuError(f"Could not reach Setu to sign in: {err.__class__.__name__}")
        if res.status_code != 200 or not res.json().get("access_token"):
            raise SetuError(f"Setu sign-in failed: {_error_text(res)}", res.status_code)
        token = res.json()["access_token"]
        _token_cache["value"] = token
        _token_cache["expires_at"] = _jwt_expiry(token)
        return token


def _request(method: str, path: str, body: Optional[dict] = None) -> Dict[str, Any]:
    if not is_configured():
        raise SetuError("Setu is not configured on the server.", 503)
    url = _clean(settings.SETU_BASE_URL).rstrip("/") + path
    for attempt in (1, 2):
        headers = {
            "Authorization": f"Bearer {_get_token(force=attempt == 2)}",
            "x-product-instance-id": _clean(settings.SETU_PRODUCT_INSTANCE_ID),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        try:
            res = _send(method, url, headers, body)
        except requests.RequestException as err:
            raise SetuError(f"Could not reach Setu: {err.__class__.__name__}")
        if res.status_code == 401 and attempt == 1:
            continue
        if not res.ok:
            raise SetuError(_error_text(res), res.status_code)
        try:
            return res.json()
        except ValueError:
            return {}
    raise SetuError("Setu rejected the sign-in token.", 401)


def create_consent(mobile: str, data_from: str, data_to: str) -> Dict[str, Any]:
    return _request("POST", "/v2/consents", {
        "consentDuration": {"unit": "MONTH", "value": "6"},
        "vua": f"{mobile}@onemoney",
        "dataRange": {"from": data_from, "to": data_to},
        "dataLife": {"unit": "MONTH", "value": "0"},
        "context": [],
    })


def get_consent(consent_id: str) -> Dict[str, Any]:
    return _request("GET", f"/v2/consents/{consent_id}")


def revoke_consent(consent_id: str) -> Dict[str, Any]:
    return _request("POST", f"/v2/consents/{consent_id}/revoke")


def create_session(consent_id: str, data_from: str, data_to: str) -> Dict[str, Any]:
    return _request("POST", "/v2/sessions", {
        "consentId": consent_id,
        "dataRange": {"from": data_from, "to": data_to},
        "format": "json",
    })


def get_session(session_id: str) -> Dict[str, Any]:
    return _request("GET", f"/v2/sessions/{session_id}")
