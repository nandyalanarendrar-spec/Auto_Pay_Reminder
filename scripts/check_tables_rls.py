import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
from app.core.security import get_supabase_client

supabase = get_supabase_client()

try:
    print("--- Inspecting Table Columns and RLS ---")
    
    # Check subscriptions
    sub_res = supabase.from_("subscriptions").select("id, user_id").limit(1).execute()
    print("Subscriptions sample row:", sub_res.data)

    # Check emis
    emi_res = supabase.from_("emis").select("id, user_id").limit(1).execute()
    print("EMIs sample row:", emi_res.data)

    # Check transactions if present
    try:
        tx_res = supabase.from_("transactions").select("id, user_id").limit(1).execute()
        print("Transactions sample row:", tx_res.data)
    except Exception as e_tx:
        print("Transactions table status:", e_tx)

except Exception as err:
    print("Error inspecting tables:", err)
