"""
Payment Database Models

This module defines the SQLAlchemy models for storing payment transactions.
The Payment model stores all transaction details including payment method specific
information in a JSON field for flexibility.

Model Design Decisions:
1. PaymentMethod as Enum: Ensures type safety and easy extension for new methods
2. Decimal for monetary values: Avoids floating-point precision issues
3. JSON for additional_item: Flexible storage for payment method specific data
4. Indexed datetime: Enables efficient sales reporting queries by time range
"""

import enum

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.sql import func

from app.database import Base


class PaymentMethod(str, enum.Enum):
    """
    Enumeration of supported payment methods.

    Each payment method has different:
    - Price modifier ranges (discounts or surcharges)
    - Points calculation rates
    - Required additional information

    This enum inherits from str to allow easy serialization and comparison.
    """

    CASH = "CASH"
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"
    VISA = "VISA"
    MASTERCARD = "MASTERCARD"
    AMEX = "AMEX"
    JCB = "JCB"
    LINE_PAY = "LINE_PAY"
    PAYPAY = "PAYPAY"
    POINTS = "POINTS"
    GRAB_PAY = "GRAB_PAY"
    BANK_TRANSFER = "BANK_TRANSFER"
    CHEQUE = "CHEQUE"


class Payment(Base):
    """
    Payment transaction model.

    Stores all information about a completed payment transaction including
    the original price, applied modifiers, calculated final price, and
    awarded points.

    Attributes:
        id: Primary key, auto-incremented
        customer_id: Identifier of the customer making the payment
        price: Original price before modifiers (Decimal for precision)
        price_modifier: Applied modifier (e.g., 0.95 for 5% discount)
        final_price: Calculated final price (price * price_modifier)
        points: Loyalty points awarded for this transaction
        payment_method: Type of payment used (from PaymentMethod enum)
        additional_item: JSON field for payment-specific data:
            - Card payments: {"last4": "1234"}
            - CASH_ON_DELIVERY: {"courier": "YAMATO"}
            - BANK_TRANSFER: {"bank": "...", "account_number": "..."}
            - CHEQUE: {"bank": "...", "cheque_number": "..."}
        datetime: When the payment was made (for sales reporting)
        created_at: When the record was created (audit purposes)

    Indexes:
        - ix_payment_datetime: For efficient time-range queries in sales reports
        - ix_payment_customer_id: For customer payment history lookups
    """

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(String(255), nullable=False, index=True)

    # Monetary values using Numeric for decimal precision
    # precision=10, scale=2 allows values up to 99,999,999.99
    price = Column(Numeric(precision=10, scale=2), nullable=False)
    price_modifier = Column(Numeric(precision=4, scale=2), nullable=False)
    final_price = Column(Numeric(precision=10, scale=2), nullable=False)
    points = Column(Integer, nullable=False, default=0)

    # Payment method and additional data
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    additional_item = Column(JSON, nullable=True)

    # Timestamps
    # datetime column is indexed for efficient time-range queries in sales reports
    datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<Payment(id={self.id}, customer={self.customer_id}, "
            f"method={self.payment_method.value}, final={self.final_price})>"
        )
