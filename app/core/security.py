from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.core.config import settings

security = HTTPBearer(auto_error=False)

# ── Singleton Supabase client (avoids re-creating HTTP connection pool on every request) ──
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase_client

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
    FastAPI dependency that extracts Supabase JWT token if present.
    If no token is provided (e.g. Swagger UI testing), falls back to the active user session.
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
            print("Supabase Auth token verify error in optional auth:", e)

    # Fallback to active OAuth user record in database
    try:
        supabase = get_supabase_client()
        res = supabase.from_("oauth_tokens").select("user_id, google_email").order("updated_at", desc=True).limit(1).execute()
        if res.data and len(res.data) > 0:
            return {
                "id": res.data[0].get("user_id"),
                "email": res.data[0].get("google_email")
            }
    except Exception as e:
        print("Fallback user lookup note:", e)

    return {
        "id": "b214d765-ddd1-4dab-b44a-0162fca19579",
        "email": "nandyalanarendrar@gmail.com"
    }



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
