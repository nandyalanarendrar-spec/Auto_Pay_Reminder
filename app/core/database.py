# SINGLE SOURCE OF TRUTH: DATABASE_URL in .env is the master database connection string for SQLAlchemy engine and migrations.
import os
from app.core.config import settings

# Retrieve DATABASE_URL from environment
DATABASE_URL = settings.DATABASE_URL or os.getenv("DATABASE_URL", "")

# A bare "postgresql://" scheme leaves SQLAlchemy to pick a default driver, and that default
# has changed across SQLAlchemy versions — some newer releases prefer psycopg (v3) over
# psycopg2, so a plain URL that worked with one SQLAlchemy version can suddenly fail with
# "No module named 'psycopg'" after a routine `pip install` picks up a newer SQLAlchemy,
# even though psycopg2-binary (what's actually in requirements.txt) is installed fine.
# Pinning the driver explicitly makes this independent of whatever SQLAlchemy version lands.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

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
    print(f"⚠️ [Database] SQLAlchemy or its driver is not installed: {imp_err!r}")
except Exception as other_err:
    print(f"⚠️ [Database] Failed to create engine: {other_err!r}")

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
