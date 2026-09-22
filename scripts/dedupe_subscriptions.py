import sys
import os
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import engine

def check_and_dedupe():
    if engine is None:
        print("No engine")
        return

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id, user_id, merchant_name, amount, next_payment_date FROM subscriptions ORDER BY created_at DESC;")).fetchall()
            print(f"Total rows in subscriptions: {len(rows)}")
            seen = set()
            to_delete = []
            for r in rows:
                key = (r[1], (r[2] or "").lower().strip())
                if key in seen:
                    to_delete.append(r[0])
                else:
                    seen.add(key)
                print("Row:", r)

            if to_delete:
                print("Deleting duplicate IDs:", to_delete)
                for did in to_delete:
                    conn.execute(text("DELETE FROM subscriptions WHERE id = :did"), {"did": did})
                conn.commit()
                print(f"Deleted {len(to_delete)} duplicate subscription rows.")
            else:
                print("No duplicate rows found in DB.")
    except Exception as err:
        print("Error checking DB:", err)

if __name__ == "__main__":
    check_and_dedupe()
