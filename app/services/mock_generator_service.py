import uuid
import random
from datetime import datetime, timedelta, date
from typing import List, Optional
from app.core.security import get_supabase_client

# Try importing Faker, with fallback random string generator
try:
    from faker import Faker
    fake = Faker('en_IN')
except ImportError:
    class DummyFaker:
        def company(self): return random.choice(["Amazon Pay", "Swiggy", "Zomato", "Uber Rides", "ATM Cash Debit"])
    fake = DummyFaker()

NOISE_MERCHANTS = [
    "Amazon Pay IN", "Swiggy Food", "Zomato Online", "Uber India", 
    "ATM Withdrawal HDFC", "Local Grocery Store", "Tea Stall UPI", 
    "BookMyShow", "HPCL Petrol Pump", "Flipkart Online"
]

import threading

_INITIALIZED_USERS_CACHE = set()
_INIT_LOCK = threading.Lock()

class MockGeneratorService:
    
    @staticmethod
    def inject_recurring_pattern(user_id: str, merchant: str, amount: float, frequency_days: int = 30, num_cycles: int = 6) -> List[dict]:
        """
        Inserts transactions following a fixed recurring pattern (~30 day gaps, identical amounts).
        Uses authentic Indian bank narration formats (e.g. 'UPI/548190/NETFLIX/paytm@ybl/Auto-Debit').
        """
        items = []
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=frequency_days * num_cycles)
        clean_uid = str(user_id).strip('"\'')
        
        for i in range(num_cycles):
            t_date = (start_date + timedelta(days=i * frequency_days + random.randint(-1, 1))).strftime("%Y-%m-%d")
            ref_num = random.randint(100000000000, 999999999999)
            narration = f"UPI/{ref_num}/{merchant.upper()}/autopay@okaxis/Auto-Debit"
            
            items.append({
                "id": str(uuid.uuid4()),
                "user_id": clean_uid,
                "merchant_name": merchant,
                "amount": float(amount),
                "transaction_date": t_date,
                "narration": narration,
                "mode": "AUTO-DEBIT",
                "is_labeled_recurring": False, # UNLABELED for detection algorithm!
                "is_labeled_emi": False
            })
        return items

    @staticmethod
    def inject_price_increase_pattern(user_id: str, merchant: str, amount_progression: List[float], frequency_days: int = 30) -> List[dict]:
        """
        Inserts transactions for subscriptions whose price increases over time.
        """
        items = []
        end_date = datetime.utcnow()
        num_cycles = len(amount_progression)
        start_date = end_date - timedelta(days=frequency_days * num_cycles)
        clean_uid = str(user_id).strip('"\'')

        for i, amt in enumerate(amount_progression):
            t_date = (start_date + timedelta(days=i * frequency_days + random.randint(-1, 1))).strftime("%Y-%m-%d")
            ref_num = random.randint(100000000000, 999999999999)
            narration = f"ACH-DEBIT/{ref_num}/{merchant.upper()}-PRICE-HIKE"

            items.append({
                "id": str(uuid.uuid4()),
                "user_id": clean_uid,
                "merchant_name": merchant,
                "amount": float(amt),
                "transaction_date": t_date,
                "narration": narration,
                "mode": "AUTO-DEBIT",
                "is_labeled_recurring": False,
                "is_labeled_emi": False
            })
        return items

    @staticmethod
    def inject_emi_pattern(user_id: str, loan_name: str, installment_amount: float, total_installments: int = 12, cycles: int = 6) -> List[dict]:
        """
        Inserts EMI-style transactions with authentic narration (e.g. 'ACH DEBIT 3/12 - HDFC HOME LOAN').
        """
        items = []
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30 * cycles)
        clean_uid = str(user_id).strip('"\'')

        for i in range(1, min(cycles, total_installments) + 1):
            t_date = (start_date + timedelta(days=(i - 1) * 30)).strftime("%Y-%m-%d")
            narration = f"ACH DEBIT {i}/{total_installments} - {loan_name.upper()}"

            items.append({
                "id": str(uuid.uuid4()),
                "user_id": clean_uid,
                "merchant_name": loan_name,
                "amount": float(installment_amount),
                "transaction_date": t_date,
                "narration": narration,
                "mode": "NEFT",
                "is_labeled_recurring": False,
                "is_labeled_emi": False
            })
        return items

    @staticmethod
    def inject_anomaly(user_id: str, anomaly_type: str) -> List[dict]:
        """
        Inserts anomaly transactions (unknown_merchant, sudden_spike, duplicate_category) for testing risk engine.
        """
        items = []
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        clean_uid = str(user_id).strip('"\'')

        if anomaly_type == "sudden_spike":
            items.append({
                "id": str(uuid.uuid4()),
                "user_id": clean_uid,
                "merchant_name": "Netflix Premium 4K",
                "amount": 199.99, # Sudden spike from normal 19.99!
                "transaction_date": today_str,
                "narration": "UPI/UNUSUAL-PRICE-SPIKE-NETFLIX",
                "mode": "AUTO-DEBIT",
                "is_labeled_recurring": False,
                "is_labeled_emi": False
            })
        elif anomaly_type == "unknown_merchant":
            items.append({
                "id": str(uuid.uuid4()),
                "user_id": clean_uid,
                "merchant_name": "UNKNOWN_BILLING_CORP_XYZ",
                "amount": 49.99,
                "transaction_date": today_str,
                "narration": "DEBIT/UNRECOGNIZED-SUSPICIOUS-MERCHANT",
                "mode": "AUTO-DEBIT",
                "is_labeled_recurring": False,
                "is_labeled_emi": False
            })
        return items

    @staticmethod
    def generate_mock_dataset(user_id: str, months: int = 6, include_emi: bool = True, include_anomaly: bool = False) -> List[dict]:
        """
        Combines noise transactions, recurring subscriptions, price hikes, and EMIs into a raw dataset.
        Persists directly to Supabase PostgreSQL table.
        """
        all_txns = []
        clean_uid = str(user_id).strip('"\'')

        # 1. Add random noise transactions (Swiggy, Amazon, Uber)
        for _ in range(months * 4):
            random_days = random.randint(1, months * 30)
            t_date = (datetime.utcnow() - timedelta(days=random_days)).strftime("%Y-%m-%d")
            merchant = random.choice(NOISE_MERCHANTS)
            all_txns.append({
                "id": str(uuid.uuid4()),
                "user_id": clean_uid,
                "merchant_name": merchant,
                "amount": round(random.uniform(5.0, 120.0), 2),
                "transaction_date": t_date,
                "narration": f"UPI/{random.randint(100000,999999)}/{merchant.replace(' ','')}",
                "mode": "UPI",
                "is_labeled_recurring": False,
                "is_labeled_emi": False
            })

        # 2. Inject recurring subscriptions (Netflix, Spotify, ChatGPT)
        all_txns.extend(MockGeneratorService.inject_recurring_pattern(clean_uid, "Netflix Premium", 649.00, 30, months))
        all_txns.extend(MockGeneratorService.inject_recurring_pattern(clean_uid, "Spotify India", 179.00, 30, months))
        all_txns.extend(MockGeneratorService.inject_recurring_pattern(clean_uid, "ChatGPT Plus", 1999.00, 30, months))

        # 3. Inject price increase pattern (Adobe CC)
        all_txns.extend(MockGeneratorService.inject_price_increase_pattern(clean_uid, "Adobe Creative Cloud", [2499.00, 2499.00, 3299.00, 3299.00, 4230.00, 4230.00]))

        # 4. Inject EMI patterns if requested
        if include_emi:
            all_txns.extend(MockGeneratorService.inject_emi_pattern(clean_uid, "iPhone 15 HDFC EMI", 4500.00, 12, months))
            all_txns.extend(MockGeneratorService.inject_emi_pattern(clean_uid, "Bajaj Finserv Electronics EMI", 2200.00, 6, min(months, 6)))

        # 5. Inject anomaly if requested
        if include_anomaly:
            all_txns.extend(MockGeneratorService.inject_anomaly(clean_uid, "sudden_spike"))
            all_txns.extend(MockGeneratorService.inject_anomaly(clean_uid, "unknown_merchant"))

        # Sort by transaction date descending
        all_txns.sort(key=lambda x: x["transaction_date"], reverse=True)

        # Sync to Supabase PostgreSQL DB
        supabase = get_supabase_client()
        try:
            supabase.from_("transactions").insert(all_txns).execute()
        except Exception as err:
            print("Supabase REST transactions insert error:", err)

        return all_txns

    @staticmethod
    def get_user_transactions(user_id: str) -> List[dict]:
        clean_uid = str(user_id).strip('"\'')
        supabase = get_supabase_client()
        try:
            res = supabase.from_("transactions").select("*").eq("user_id", clean_uid).order("transaction_date", desc=True).execute()
            if res.data and len(res.data) > 0:
                return res.data
        except Exception as err:
            print("Supabase REST transactions select error:", err)

        return []

    @staticmethod
    def is_mock_data_initialized(user_id: str) -> bool:
        clean_uid = str(user_id).strip('"\'')
        if clean_uid in _INITIALIZED_USERS_CACHE:
            return True

        supabase = get_supabase_client()

        # 1. Check user_settings table
        try:
            res = supabase.from_("user_settings").select("mock_data_initialized").eq("user_id", clean_uid).execute()
            if res.data and len(res.data) > 0:
                is_init = bool(res.data[0].get("mock_data_initialized", False))
                if is_init:
                    _INITIALIZED_USERS_CACHE.add(clean_uid)
                    return True
        except Exception:
            pass

        # 2. Check users table
        try:
            res = supabase.from_("users").select("mock_data_initialized").eq("id", clean_uid).execute()
            if res.data and len(res.data) > 0:
                is_init = bool(res.data[0].get("mock_data_initialized", False))
                if is_init:
                    _INITIALIZED_USERS_CACHE.add(clean_uid)
                    return True
        except Exception:
            pass

        # 3. Check if user already has any existing subscriptions in DB
        try:
            res = supabase.from_("subscriptions").select("id").eq("user_id", clean_uid).limit(1).execute()
            if res.data and len(res.data) > 0:
                _INITIALIZED_USERS_CACHE.add(clean_uid)
                return True
        except Exception:
            pass

        return False

    @staticmethod
    def set_mock_data_initialized(user_id: str, initialized: bool = True):
        clean_uid = str(user_id).strip('"\'')
        if initialized:
            _INITIALIZED_USERS_CACHE.add(clean_uid)
        elif clean_uid in _INITIALIZED_USERS_CACHE:
            _INITIALIZED_USERS_CACHE.remove(clean_uid)

        supabase = get_supabase_client()
        payload = {
            "user_id": clean_uid,
            "mock_data_initialized": initialized,
            "updated_at": datetime.utcnow().isoformat()
        }
        try:
            supabase.from_("user_settings").upsert(payload, on_conflict="user_id").execute()
        except Exception:
            pass

        try:
            supabase.from_("users").update({"mock_data_initialized": initialized}).eq("id", clean_uid).execute()
        except Exception:
            pass

    @staticmethod
    def ensure_one_time_mock_initialization(user_id: str) -> bool:
        """
        Guarantees mock subscriptions, EMIs, and raw transactions are seeded EXACTLY ONCE per user.
        Uses thread lock to prevent concurrent double-initialization (e.g., React 18 StrictMode double-fetch).
        """
        clean_uid = str(user_id).strip('"\'')
        
        with _INIT_LOCK:
            if MockGeneratorService.is_mock_data_initialized(clean_uid):
                return False

            # First time user initialization:
            print(f"🌱 Initializing one-time mock dataset for user {clean_uid}...")
            
            # Mark initialized = True FIRST to prevent concurrent re-entry
            _INITIALIZED_USERS_CACHE.add(clean_uid)

            # 1. Seed Subscriptions
            from app.services.subscription_service import SubscriptionService
            SubscriptionService.seed_initial_mock_subscriptions(clean_uid)

            # 2. Seed EMIs
            from app.services.emi_service import EMIService
            EMIService.seed_initial_mock_emis(clean_uid)

            # 3. Seed Raw Bank Transactions
            MockGeneratorService.generate_mock_dataset(clean_uid, months=6, include_emi=True, include_anomaly=False)

            # 4. Save initialized state to DB
            MockGeneratorService.set_mock_data_initialized(clean_uid, True)
            return True

    # Alias for backward compatibility
    initialize_user_mock_data_if_needed = ensure_one_time_mock_initialization

