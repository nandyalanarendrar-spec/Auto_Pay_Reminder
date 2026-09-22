import uuid
from sqlalchemy import Column, String, Numeric, Integer, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

# EMI Model: Tracks equated monthly installments for loans, device financing, or credit card EMIs
class EMI(Base):
    __tablename__ = "emis"

    # Primary key UUID for EMI loan record
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Foreign key referencing registered user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Loan or financing service name (e.g. iPhone EMI, HDFC Home Loan)
    loan_name = Column(String(255), nullable=False)
    # Total count of installments in loan agreement
    total_installments = Column(Integer, nullable=False)
    # Number of installments completed so far
    installments_paid = Column(Integer, default=0)
    # Fixed payment amount per installment
    installment_amount = Column(Numeric(10, 2), nullable=False)
    # Date loan EMI started
    start_date = Column(Date, nullable=True)
    # Next upcoming due date for EMI installment
    next_due_date = Column(Date, nullable=False, index=True)
    # Remaining total balance left to pay
    remaining_amount = Column(Numeric(10, 2), nullable=False)
    # Status: active, completed, defaulted
    status = Column(String(50), default="active")
    # Google Calendar event tracking fields
    calendar_event_id = Column(String(255), nullable=True, index=True)
    calendar_id = Column(String(255), default="primary")
    calendar_sync_status = Column(String(50), default="PENDING")
    calendar_sync_error = Column(String(1024), nullable=True)
    calendar_last_synced_at = Column(DateTime, nullable=True)
    # Record creation timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="emis")

