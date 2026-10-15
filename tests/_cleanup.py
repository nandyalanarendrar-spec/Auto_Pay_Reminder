"""Shared test cleanup: remove the throwaway auth user a fixture created."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def delete_auth_user(user_id: str) -> bool:
    """
    Uses a fresh secret-key client on purpose: the shared client becomes the signed-up user's session after
    sign_up(), and that session is not allowed to delete accounts.
    """
    try:
        from supabase import create_client
        from app.core.config import settings

        create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY).auth.admin.delete_user(str(user_id))
        return True
    except Exception as err:
        print("test cleanup: could not delete auth user:", err.__class__.__name__)
        return False
