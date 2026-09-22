import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
from app.core.security import get_supabase_client

supabase = get_supabase_client()

try:
    res = supabase.from_("notification_logs").select("*").execute()
    print("--- Notification Logs Table State in Supabase DB ---")
    print(f"Total Rows Count: {len(res.data or [])}")
    for row in (res.data or [])[:10]:
        print("  Row:", row)
except Exception as e:
    print("Error querying notification_logs table:", e)
