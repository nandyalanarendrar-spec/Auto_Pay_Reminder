import sys
import os
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def main():
    print("=" * 80)
    print("📋 SANITY CHECK: PUBLIC SCHEMA TABLES DIRECT SQL AUDIT")
    print("=" * 80)

    db_url = getattr(settings, "DATABASE_URL", None)
    if not db_url:
        print("❌ DATABASE_URL missing")
        return

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    try:
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
        cur.execute(query)
        tables = [r[0] for r in cur.fetchall()]

        print(f"\nSQL Executed: {query}\n")
        print(f"Raw Result List ({len(tables)} public tables total):")
        print("--------------------------------------------------")
        for idx, t in enumerate(tables, 1):
            print(f"  {idx}. {t}")
        print("--------------------------------------------------")

        expected_tables = ["device_tokens", "emis", "notification_logs", "oauth_tokens", "subscriptions", "transactions"]
        missing = [t for t in expected_tables if t not in tables]

        if not missing:
            print("\n✅ SANITY CHECK PASSED: All 6 required tables physically exist in Supabase PostgreSQL!")
        else:
            print(f"\n❌ WARNING: Missing tables: {missing}")

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
