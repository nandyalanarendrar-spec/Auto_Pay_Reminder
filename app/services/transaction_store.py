import uuid
from typing import Any, Dict, List, Optional

from app.core.security import get_supabase_client

SOURCE_DEMO = "demo"
SOURCE_SETU = "setu_aa"


def clean_user_id(user_id: Any) -> Optional[str]:
    clean = str(user_id).strip("\"'")
    try:
        uuid.UUID(clean)
    except (ValueError, AttributeError, TypeError):
        return None
    return clean


class TransactionStore:
    """Single place every bank-transaction source (Setu AA, demo bank, manual) reads and writes."""

    @staticmethod
    def get_user_transactions(user_id: Any, source: Optional[str] = None) -> List[dict]:
        uid = clean_user_id(user_id)
        if not uid:
            return []
        try:
            query = get_supabase_client().from_("transactions").select("*").eq("user_id", uid)
            if source:
                query = query.eq("source", source)
            res = query.order("transaction_date", desc=True).limit(5000).execute()
            return res.data or []
        except Exception as err:
            print("TransactionStore read error:", err)
            return []

    @staticmethod
    def insert_many(rows: List[Dict[str, Any]]) -> int:
        """Insert rows, skipping any (user_id, external_id) that already exists. Returns rows actually added."""
        if not rows:
            return 0
        added = 0
        supabase = get_supabase_client()
        for i in range(0, len(rows), 200):
            chunk = rows[i:i + 200]
            try:
                res = supabase.from_("transactions").upsert(
                    chunk, on_conflict="user_id,external_id", ignore_duplicates=True
                ).execute()
                added += len(res.data or [])
            except Exception as err:
                print("TransactionStore insert error:", err)
        return added

    @staticmethod
    def delete_by_source(user_id: Any, source: str) -> int:
        uid = clean_user_id(user_id)
        if not uid:
            return 0
        try:
            res = get_supabase_client().from_("transactions").delete().eq("user_id", uid).eq("source", source).execute()
            return len(res.data or [])
        except Exception as err:
            print("TransactionStore delete error:", err)
            return 0

    @staticmethod
    def count_by_source(user_id: Any, source: str) -> int:
        uid = clean_user_id(user_id)
        if not uid:
            return 0
        try:
            res = (
                get_supabase_client().from_("transactions")
                .select("id", count="exact").eq("user_id", uid).eq("source", source).limit(1).execute()
            )
            return res.count or 0
        except Exception as err:
            print("TransactionStore count error:", err)
            return 0

    @staticmethod
    def user_ids_with_source(source: str) -> List[str]:
        try:
            res = get_supabase_client().from_("transactions").select("user_id").eq("source", source).limit(5000).execute()
            return sorted({str(r["user_id"]) for r in (res.data or []) if r.get("user_id")})
        except Exception as err:
            print("TransactionStore user listing error:", err)
            return []
