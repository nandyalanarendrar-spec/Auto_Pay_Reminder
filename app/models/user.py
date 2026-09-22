import uuid
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

# User Model: Stores registered user account details and credentials for authentication
class User(Base):
    __tablename__ = "users"

    # Unique user identifier (UUID primary key)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # User email address used for login and notifications
    email = Column(String(255), unique=True, nullable=False, index=True)
    # Securely hashed user password
    password_hash = Column(String(255), nullable=False)
    # User display name
    name = Column(String(255), nullable=True)
    # Account status flag
    is_active = Column(Boolean, default=True)
    # One-time mock data initialization flag
    mock_data_initialized = Column(Boolean, default=False, nullable=False)
    # Timestamp when user registered
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    emis = relationship("EMI", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
