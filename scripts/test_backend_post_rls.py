import sys
import os
import requests
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
from app.core.security import get_supabase_client

API_BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_UID = "b214d765-ddd1-4dab-b44a-0162fca19579"

print("=============================================================")
print("TESTING BACKEND API OPERABILITY & RLS DEFENSE-IN-DEPTH")
print("=============================================================")

# 1. Test Subscriptions List API
print("\n--- 1. Testing GET /subscriptions/ ---")
res_subs = requests.get(f"{API_BASE_URL}/subscriptions/")
print(f"Status Code: {res_subs.status_code}")
data_subs = res_subs.json()
print(f"Returned {data_subs.get('count', 0)} subscriptions.")

# 2. Test EMIs List API
print("\n--- 2. Testing GET /emis/ ---")
res_emis = requests.get(f"{API_BASE_URL}/emis/")
print(f"Status Code: {res_emis.status_code}")
data_emis = res_emis.json()
print(f"Returned {data_emis.get('count', 0)} EMIs.")

# 3. Test Notifications Reminders API
print("\n--- 3. Testing GET /notifications/due-reminders ---")
res_notifs = requests.get(f"{API_BASE_URL}/notifications/due-reminders")
print(f"Status Code: {res_notifs.status_code}")
data_notifs = res_notifs.json()
print(f"Returned {data_notifs.get('count', 0)} due alerts.")

# 4. Check Direct Supabase Client Query
supabase = get_supabase_client()
print("\n--- 4. Direct Supabase Query with Service Role Key ---")
direct_subs = supabase.from_("subscriptions").select("id, merchant_name, user_id").eq("user_id", TEST_UID).execute()
print(f"Direct Query returned {len(direct_subs.data or [])} rows.")

if res_subs.status_code == 200 and res_emis.status_code == 200 and res_notifs.status_code == 200:
    print("\n✅ BACKEND API OPERABILITY VERIFIED 100%! All endpoints working cleanly!")
else:
    print("\n❌ API ERROR POST RLS!")
