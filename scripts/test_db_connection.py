import sys
import os
from sqlalchemy import text

# Add root project path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import engine
from app.core.config import settings

def test_connection():
    print("==================================================")
    print("Testing Supabase PostgreSQL Connection...")
    print("==================================================")
    
    if engine is None:
        print("❌ DATABASE_URL is missing or not set in .env")
        print("Please add DATABASE_URL to your .env file.")
        print("Example: DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.bpewdueusbsqyzvjjeqe.supabase.co:5432/postgres")
        return False

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1;"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✅ SUCCESS: Successfully connected to Supabase PostgreSQL!")
                print("Query 'SELECT 1' returned 1.")
                return True
    except Exception as err:
        print("❌ CONNECTION FAILED:")
        print(err)
        return False

if __name__ == "__main__":
    test_connection()
