import uuid
from sqlalchemy import Column, String, Numeric, Boolean, Date, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

# Subscription Model: Tracks active, trial, or cancelled recurring services & autopay dates
class Subscription(Base):
    __tablename__ = "subscriptions"

    # Primary key UUID for subscription record
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Foreign key referencing registered user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Service provider or merchant name (e.g. Netflix, ChatGPT, Spotify)
    merchant_name = Column(String(255), nullable=False, index=True)
    # Category (Streaming, Software, Gym, Utilities, etc.)
    category = Column(String(100), default="General")
    # Cost amount per billing cycle
    amount = Column(Numeric(10, 2), nullable=False)
    # Billing frequency (monthly, yearly, weekly)
    billing_frequency = Column(String(50), default="monthly")
    # Date subscription started
    start_date = Column(Date, nullable=True)
    # Next upcoming payment / debit date
    next_payment_date = Column(Date, nullable=False, index=True)
    # Status: active, cancelled, trial, paused
    status = Column(String(50), default="active")
    # Boolean flag indicating if charge recurs automatically
    is_recurring = Column(Boolean, default=True)
    # Autopay active status on user's bank/card
    autopay_enabled = Column(Boolean, default=True)
    # Free trial tracking fields
    trial_start_date = Column(Date, nullable=True)
    trial_end_date = Column(Date, nullable=True)
    expected_first_payment_date = Column(Date, nullable=True)
    is_free_trial = Column(Boolean, default=False)
    # Calculated risk score (1 to 100) based on free trials and cost
    risk_score = Column(Integer, default=10)
    # Vaulted receipt image or PDF file URL
    receipt_url = Column(String(1024), nullable=True)
    # Source of subscription: user_added, detected, imported
    source = Column(String(50), default="user_added")
    # Google Calendar event tracking fields
    calendar_event_id = Column(String(255), nullable=True, index=True)
    calendar_id = Column(String(255), default="primary")
    calendar_sync_status = Column(String(50), default="PENDING")
    calendar_sync_error = Column(String(1024), nullable=True)
    calendar_last_synced_at = Column(DateTime, nullable=True)
    # Record creation timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
