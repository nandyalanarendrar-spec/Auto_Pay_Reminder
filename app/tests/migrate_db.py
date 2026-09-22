import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import engine

def migrate_database():
    print("Running database migrations for Supabase PostgreSQL tables...")
    with engine.connect() as conn:
        # Add source column to subscriptions table if not exists
        conn.execute(text("ALTER TABLE public.subscriptions ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'user_added';"))
        conn.commit()
        print("✅ Added 'source' column to subscriptions table successfully (if it didn't exist).")

if __name__ == "__main__":
    migrate_database()
