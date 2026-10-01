# SINGLE SOURCE OF TRUTH: DATABASE_URL in .env is the master database connection string for SQLAlchemy engine and migrations.
import os
from app.core.config import settings

# Retrieve DATABASE_URL from environment
DATABASE_URL = settings.DATABASE_URL or os.getenv("DATABASE_URL", "")

# TEMPORARY DIAGNOSTIC — remove once the Render "DATABASE_URL not initialized" mystery is
# resolved. Prints only length/prefix, never the real value (password included in the URL).
print(f"[DB DIAGNOSTIC] settings.DATABASE_URL len={len(settings.DATABASE_URL or '')} "
      f"os.getenv('DATABASE_URL') len={len(os.getenv('DATABASE_URL', ''))} "
      f"resolved DATABASE_URL len={len(DATABASE_URL)} "
      f"prefix={DATABASE_URL[:15]!r}")

engine = None
SessionLocal = None
Base = None

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker, declarative_base

    Base = declarative_base()

    if DATABASE_URL and not DATABASE_URL.startswith("your_"):
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

except ImportError as imp_err:
    print(f"[DB DIAGNOSTIC] SQLAlchemy ImportError: {imp_err!r}")
except Exception as other_err:
    print(f"[DB DIAGNOSTIC] create_engine() failed (not an ImportError): {other_err!r}")

# FastAPI Dependency for Database Session
def get_db():
    if SessionLocal is None:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
