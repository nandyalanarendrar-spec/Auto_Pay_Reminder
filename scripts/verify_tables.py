import sys
import os
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import engine

def verify_tables():
    print("==================================================")
    print("Querying Supabase Public Database Tables...")
    print("==================================================")
    
    if engine is None:
        print("❌ Database engine not initialized. Check DATABASE_URL in .env")
        return

    try:
        with engine.connect() as conn:
            query = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
            result = conn.execute(query)
            tables = [row[0] for row in result.fetchall()]
            
            print(f"✅ Found {len(tables)} table(s) in 'public' schema:\n")
            for t in tables:
                print(f"  • {t}")
                
            return tables
    except Exception as e:
        print("❌ Error querying database tables:", e)

if __name__ == "__main__":
    verify_tables()
