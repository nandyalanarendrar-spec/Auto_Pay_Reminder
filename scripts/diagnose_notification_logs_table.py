import sys
import os
import urllib.parse
import psycopg2
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def main():
    print("=" * 80)
    print("🔍 DIAGNOSTIC AUDIT: NOTIFICATION_LOGS TABLE PHYSICAL DB CHECK")
    print("=" * 80)

    db_url = getattr(settings, "DATABASE_URL", None)
    print(f"DATABASE_URL configured: {db_url[:45]}..." if db_url else "No DATABASE_URL found!")

    if not db_url:
        print("❌ ERROR: DATABASE_URL not set in environment!")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        print("✅ Direct PostgreSQL Connection Established Successfully!")

        # 1. Check if table physically exists in information_schema.tables
        cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name = 'notification_logs';")
        rows = cur.fetchall()
        print(f"\n--- STEP 1: Querying information_schema.tables for 'notification_logs' ---")
        print(f"Raw Output: {rows}")

        # Also list all public tables in database
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
        all_public_tables = [r[0] for r in cur.fetchall()]
        print(f"\nAll Public Tables in Supabase Database ({len(all_public_tables)} total):")
        print(f"  {all_public_tables}")

        if not rows:
            print("\n❌ DIAGNOSIS: CASE 3 — Table 'notification_logs' DOES NOT PHYSICALLY EXIST in this Supabase database!")
            print("The earlier migration (005_create_notification_logs_table.sql) was never executed against this database instance.")
        else:
            print("\n✅ DIAGNOSIS: CASE 2 — Table 'notification_logs' PHYSICALLY EXISTS in Supabase PostgreSQL!")
            
            # Fetch column structure
            cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'notification_logs' ORDER BY ordinal_position;")
            cols = cur.fetchall()
            print("\nColumn Definitions:")
            for col_name, col_type in cols:
                print(f"  - {col_name}: {col_type}")

            # Check row count directly via SQL
            cur.execute("SELECT count(*) FROM notification_logs;")
            count = cur.fetchone()[0]
            print(f"\nPhysical Row Count in 'notification_logs': {count}")

            # Execute NOTIFY pgrst, 'reload schema'; to refresh Supabase PostgREST cache
            print("\nExecuting: NOTIFY pgrst, 'reload schema';")
            cur.execute("NOTIFY pgrst, 'reload schema';")
            conn.commit()
            print("✅ NOTIFY pgrst, 'reload schema'; executed & committed!")

        cur.close()
        conn.close()

    except Exception as err:
        print("PostgreSQL Query Error:", err)

if __name__ == "__main__":
    main()
