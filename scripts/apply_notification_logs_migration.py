import sys
import os
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def apply_migration():
    print("=" * 80)
    print("🚀 APPLYING MIGRATION: 005_create_notification_logs_table.sql")
    print("=" * 80)

    db_url = getattr(settings, "DATABASE_URL", None)
    if not db_url:
        print("❌ DATABASE_URL missing")
        return

    sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations", "005_create_notification_logs_table.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    try:
        print("Executing SQL Migration...")
        cur.execute(sql_content)
        conn.commit()
        print("✅ SQL Migration Executed & Committed Successfully!")

        # Notify PostgREST to reload schema
        cur.execute("NOTIFY pgrst, 'reload schema';")
        conn.commit()
        print("✅ NOTIFY pgrst, 'reload schema'; Executed & Committed!")

        # Verify physical table creation
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
        tables = [r[0] for r in cur.fetchall()]
        print(f"\nUpdated Public Tables ({len(tables)} total):")
        print(f"  {tables}")

        assert "notification_logs" in tables, "Migration failed to create notification_logs table!"
        print("\n🎉 'notification_logs' TABLE PHYSICALLY CREATED IN SUPABASE DB!")

    except Exception as err:
        print("❌ Migration error:", err)
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    apply_migration()
