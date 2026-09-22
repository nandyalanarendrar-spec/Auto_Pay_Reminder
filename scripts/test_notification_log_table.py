import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
from app.core.security import get_supabase_client

supabase = get_supabase_client()

try:
    # Try selecting from notification_logs table
    res = supabase.from_("notification_logs").select("*").limit(5).execute()
    print("notification_logs table exists! Data:", res.data)
except Exception as e:
    print("notification_logs table query result:", e)
