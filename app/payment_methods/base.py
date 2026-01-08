"""
Base Payment Method - Strategy Pattern Interface

This module defines the abstract base class for all payment methods.
Each payment method must implement validation and calculation logic.

The Strategy Pattern is used here because:
1. Different payment methods have different validation rules
2. Price modifier ranges vary by payment method
3. Points calculation rates differ between methods
4. Additional data requirements are payment method specific

By using this pattern, adding a new payment method only requires:
1. Creating a new class that inherits from BasePaymentMethod
2. Registering it in the PaymentMethodFactory
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Optional, Tuple


class PaymentMethodError(Exception):
    """
    Custom exception for payment method validation errors.

    Attributes:
        message: Human-readable error description
        field: Optional field name that caused the error
    """

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class BasePaymentMethod(ABC):
    """
    Abstract base class for payment method strategies.

    Each payment method implementation must define:
    - min_modifier: Minimum allowed price modifier (e.g., 0.9 for 10% discount)
    - max_modifier: Maximum allowed price modifier (e.g., 1.02 for 2% surcharge)
    - points_rate: Rate for calculating loyalty points (e.g., 0.05 for 5%)

    Methods to implement:
    - validate_additional_item: Validate payment-specific additional data
    """

    # Subclasses must define these class attributes
    min_modifier: Decimal
    max_modifier: Decimal
    points_rate: Decimal

    @abstractmethod
    def validate_additional_item(self, additional_item: Optional[dict]) -> dict:
        """
        Validate and process additional payment-specific data.

        Args:
            additional_item: Dictionary with payment-specific fields
                - Card payments: {"last4": "1234"}
                - CASH_ON_DELIVERY: {"courier": "YAMATO"}
                - BANK_TRANSFER: {"bank": "...", "account_number": "..."}
                - CHEQUE: {"bank": "...", "cheque_number": "..."}

        Returns:
            dict: Validated and potentially sanitized additional item data

        Raises:
            PaymentMethodError: If validation fails
        """
        pass

    def validate_price_modifier(self, price_modifier: Decimal) -> None:
        """
        Validate that the price modifier is within the allowed range.

        Each payment method has a specific range of allowed modifiers.
        For example:
        - CASH: 0.9 to 1.0 (up to 10% discount)
        - AMEX: 0.98 to 1.01 (2% discount to 1% surcharge)

        Args:
            price_modifier: The modifier to validate

        Raises:
            PaymentMethodError: If modifier is outside allowed range
        """
        if price_modifier < self.min_modifier or price_modifier > self.max_modifier:
            raise PaymentMethodError(
                f"Price modifier must be between {self.min_modifier} and "
                f"{self.max_modifier} for this payment method. Got: {price_modifier}",
                field="priceModifier"
            )

    def calculate_final_price(self, price: Decimal, price_modifier: Decimal) -> Decimal:
        """
        Calculate the final price after applying the modifier.

        Args:
            price: Original price before modification
            price_modifier: Multiplier to apply (e.g., 0.95 for 5% off)

        Returns:
            Decimal: Final price rounded to 2 decimal places
        """
        return (price * price_modifier).quantize(Decimal("0.01"))

    def calculate_points(self, price: Decimal) -> int:
        """
        Calculate loyalty points based on the original price.

        Points are always calculated from the original price, not the final price.
        This ensures customers get fair points even with discounts.

        Args:
            price: Original price before modification

        Returns:
            int: Number of points to award (truncated, not rounded)
        """
        return int(price * self.points_rate)

    def process(
        self,
        price: Decimal,
        price_modifier: Decimal,
        additional_item: Optional[dict]
    ) -> Tuple[Decimal, int, dict]:
        """
        Process a payment with full validation.

        This is the main entry point for payment processing. It:
        1. Validates the price modifier is within range
        2. Validates additional payment-specific data
        3. Calculates final price and points

        Args:
            price: Original price
            price_modifier: Price modifier to apply
            additional_item: Payment-specific additional data

        Returns:
            Tuple containing:
            - final_price: Decimal - Calculated final price
            - points: int - Loyalty points to award
            - validated_additional_item: dict - Validated additional data

        Raises:
            PaymentMethodError: If any validation fails
        """
        # Validate inputs
        self.validate_price_modifier(price_modifier)
        validated_additional_item = self.validate_additional_item(additional_item)

        # Calculate results
        final_price = self.calculate_final_price(price, price_modifier)
        points = self.calculate_points(price)

        return final_price, points, validated_additional_item
