import uuid
from sqlalchemy import Column, String, Numeric, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

# Transaction Model: Stores raw bank statement debits for recurring payment detection algorithms
class Transaction(Base):
    __tablename__ = "transactions"

    # Primary key UUID for transaction record
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Foreign key referencing registered user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Merchant or recipient name extracted from narration
    merchant_name = Column(String(255), nullable=False, index=True)
    # Amount debited
    amount = Column(Numeric(10, 2), nullable=False)
    # Transaction date
    transaction_date = Column(Date, nullable=False, index=True)
    # Full bank statement narration / description text
    narration = Column(Text, nullable=True)
    # Payment mode: UPI, NEFT, AUTO-DEBIT, CREDIT_CARD
    mode = Column(String(50), default="AUTO-DEBIT")
    # Detection algorithm flag: True if algorithm identified recurring subscription
    is_labeled_recurring = Column(Boolean, default=False)
    # Detection algorithm flag: True if algorithm identified EMI installment
    is_labeled_emi = Column(Boolean, default=False)
    # Record creation timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="transactions")
