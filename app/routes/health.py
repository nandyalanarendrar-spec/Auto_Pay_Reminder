import urllib.parse
from fastapi import APIRouter, Depends
from app.core.config import settings

router = APIRouter()

def get_redacted_db_host() -> str:
    db_url = settings.DATABASE_URL or ""
    if not db_url:
        return "not_configured"
    try:
        parsed = urllib.parse.urlparse(db_url)
        return parsed.hostname or "unknown_host"
    except Exception:
        return "invalid_url"

@router.get("/health")
def health_check():
    db_status = "not_configured"
    db_host = get_redacted_db_host()
    tables_found = []
    
    try:
        from sqlalchemy import text
        from app.core.database import engine
        if engine is not None:
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")).fetchall()
                    tables_found = [row[0] for row in result]
                    if len(tables_found) > 0:
                        db_status = "connected"
            except Exception as e:
                db_status = f"error: {str(e)}"
    except ImportError:
        db_status = "sqlalchemy_not_installed"

    expected_core_tables = ["subscriptions", "emis", "transactions"]
    verified_count = sum(1 for t in expected_core_tables if t in tables_found)

    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "database": db_status,
        "database_host": db_host,
        "tables_verified": f"{verified_count}/{len(expected_core_tables)} core tables",
        "public_tables": tables_found,
        "supabase_url": settings.SUPABASE_URL
    }
