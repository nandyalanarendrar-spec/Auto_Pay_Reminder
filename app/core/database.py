# SINGLE SOURCE OF TRUTH: DATABASE_URL in .env is the master database connection string for SQLAlchemy engine and migrations.
import os
from app.core.config import settings

# Retrieve DATABASE_URL from environment
DATABASE_URL = settings.DATABASE_URL or os.getenv("DATABASE_URL", "")

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

except ImportError:
    print("SQLAlchemy is being installed...")

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
