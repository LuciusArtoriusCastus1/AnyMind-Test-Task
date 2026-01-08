"""
Payment Methods Package

This package implements the Strategy Pattern for handling different payment methods.
Each payment method has its own validation rules, price modifier ranges, and points
calculation logic.

Architecture:
- BasePaymentMethod: Abstract base class defining the interface
- Concrete classes: One for each payment method type
- PaymentMethodFactory: Factory for creating the correct strategy

This design allows:
1. Easy addition of new payment methods without modifying existing code
2. Isolated testing of each payment method's logic
3. Clear separation of concerns
"""

from app.payment_methods.base import BasePaymentMethod
from app.payment_methods.factory import PaymentMethodFactory, get_payment_method

__all__ = ["BasePaymentMethod", "PaymentMethodFactory", "get_payment_method"]
