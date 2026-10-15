from typing import Optional, Any

try:
    from fastapi import Depends, HTTPException, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
except ImportError:
    def Depends(f=None): return None
    class HTTPException(Exception): pass
    class status: HTTP_401_UNAUTHORIZED = 401
    class HTTPBearer:
        def __init__(self, **kw): pass
    class HTTPAuthorizationCredentials: pass

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = Any

from app.core.config import settings

security = HTTPBearer(auto_error=False)

# ── Singleton Supabase client (avoids re-creating HTTP connection pool on every request) ──
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        if create_client is None:
            return None
        _supabase_client = _build_supabase_client()
    return _supabase_client


def _build_supabase_client() -> Client:
    """
    supabase-py defaults to HTTP/2. Supabase closes idle HTTP/2 connections, and the first request
    that reuses the dead connection fails with "ConnectionTerminated" (a 500 for the user, fine on
    the next try). Plain HTTP/1.1 with a short keep-alive and connect retries avoids that.
    """
    try:
        import httpx
        from supabase import ClientOptions

        http = httpx.Client(
            http2=False,
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=10, keepalive_expiry=20.0),
            transport=httpx.HTTPTransport(retries=2),
        )
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY, options=ClientOptions(httpx_client=http))
    except Exception as err:
        print(f"Supabase client: falling back to default HTTP settings ({err.__class__.__name__}: {err})")
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """
    FastAPI dependency that extracts and verifies Supabase JWT token from Authorization header.
    Returns authenticated user object or falls back to active session user.
    """
    if credentials and credentials.credentials:
        token = credentials.credentials
        try:
            supabase = get_supabase_client()
            user_response = supabase.auth.get_user(token)
            if user_response and user_response.user:
                user = user_response.user
                return {
                    "id": user.id,
                    "email": user.email,
                    "metadata": user.user_metadata
                }
        except Exception as e:
            print("Supabase Auth token verify error:", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials. Authorization Bearer token missing.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """
    Kept for the routes that already depend on it, but it is now strict: a valid Supabase
    token is required. It previously fell back to the most recently connected account (and
    finally a hardcoded owner id) for requests without a token, which let anyone read or
    change another person's data.
    """
    return get_current_user(credentials)


ADMIN_EMAILS = ["nandyalanarendrar@gmail.com", "nnrreddy.123456789@gmail.com", "admin@autopayguard.com"]

def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    FastAPI dependency that enforces admin access control.
    Checks if is_admin flag in user_metadata is True, role is 'admin', or email is in ADMIN_EMAILS.
    Raises HTTP 403 Forbidden if user is not an administrator.
    """
    email = (current_user.get("email") or "").lower()
    metadata = current_user.get("metadata") or {}
    is_admin = metadata.get("is_admin", False) or metadata.get("role") == "admin" or email in ADMIN_EMAILS
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privilege required. Access denied."
        )
    return current_user
