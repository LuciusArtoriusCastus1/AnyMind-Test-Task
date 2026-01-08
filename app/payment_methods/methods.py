"""
Concrete Payment Method Implementations

This module contains all payment method strategy implementations.
Each class handles the specific validation and business rules for its payment type.

Payment Methods Overview:
-------------------------
| Method          | Modifier Range | Points | Additional Data Required    |
|-----------------|----------------|--------|------------------------------|
| CASH            | 0.9 - 1.0      | 5%     | None                         |
| CASH_ON_DELIVERY| 1.0 - 1.02     | 5%     | courier (YAMATO/SAGAWA)      |
| VISA            | 0.95 - 1.0     | 3%     | last4 (4 digits)             |
| MASTERCARD      | 0.95 - 1.0     | 3%     | last4 (4 digits)             |
| AMEX            | 0.98 - 1.01    | 2%     | last4 (4 digits)             |
| JCB             | 0.95 - 1.0     | 5%     | last4 (4 digits)             |
| LINE_PAY        | 1.0 - 1.0      | 1%     | None                         |
| PAYPAY          | 1.0 - 1.0      | 1%     | None                         |
| POINTS          | 1.0 - 1.0      | 0%     | None                         |
| GRAB_PAY        | 1.0 - 1.0      | 1%     | None                         |
| BANK_TRANSFER   | 1.0 - 1.0      | 0%     | bank, account_number         |
| CHEQUE          | 0.9 - 1.0      | 0%     | bank, cheque_number          |
"""

import re
from decimal import Decimal
from typing import Optional

from app.payment_methods.base import BasePaymentMethod, PaymentMethodError


class CashPayment(BasePaymentMethod):
    """
    Cash payment method.

    - Allows discounts up to 10% (modifier 0.9 to 1.0)
    - Awards 5% points on original price
    - No additional data required
    """

    min_modifier = Decimal("0.9")
    max_modifier = Decimal("1.0")
    points_rate = Decimal("0.05")

    def validate_additional_item(self, additional_item: Optional[dict]) -> dict:
        """Cash payments don't require additional data."""
        return additional_item or {}


class CashOnDeliveryPayment(BasePaymentMethod):
    """
    Cash on Delivery (COD) payment method.

    - Allows surcharges up to 2% (modifier 1.0 to 1.02)
    - Awards 5% points on original price
    - Requires courier service selection (YAMATO or SAGAWA only)
    """

    min_modifier = Decimal("1.0")
    max_modifier = Decimal("1.02")
    points_rate = Decimal("0.05")

    # Valid courier services for COD
    VALID_COURIERS = {"YAMATO", "SAGAWA"}

    def validate_additional_item(self, additional_item: Optional[dict]) -> dict:
        """
        Validate courier service selection.

        Args:
            additional_item: Must contain {"courier": "YAMATO"} or {"courier": "SAGAWA"}

        Raises:
            PaymentMethodError: If courier is missing or invalid
        """
        if not additional_item or "courier" not in additional_item:
            raise PaymentMethodError(
                "Cash on delivery requires a courier service. "
                "Please provide 'courier' in additionalItem.",
                field="additionalItem.courier"
            )

        courier = additional_item["courier"].upper()
        if courier not in self.VALID_COURIERS:
            raise PaymentMethodError(
                f"Invalid courier service '{courier}'. "
                f"Valid options are: {', '.join(sorted(self.VALID_COURIERS))}",
                field="additionalItem.courier"
            )

        return {"courier": courier}


class CardPaymentBase(BasePaymentMethod):
    """
    Base class for credit/debit card payments.

    All card payments require the last 4 digits of the card number
    for identification and receipt purposes.
    """

    def validate_additional_item(self, additional_item: Optional[dict]) -> dict:
        """
        Validate card's last 4 digits.

        Args:
            additional_item: Must contain {"last4": "1234"}

        Raises:
            PaymentMethodError: If last4 is missing or not exactly 4 digits
        """
        if not additional_item or "last4" not in additional_item:
            raise PaymentMethodError(
                "Card payments require the last 4 digits of the card. "
                "Please provide 'last4' in additionalItem.",
                field="additionalItem.last4"
            )

        last4 = str(additional_item["last4"])

        # Validate format: exactly 4 digits
        if not re.match(r"^\d{4}$", last4):
            raise PaymentMethodError(
                f"Invalid card last4 format '{last4}'. Must be exactly 4 digits.",
                field="additionalItem.last4"
            )

        return {"last4": last4}


class VisaPayment(CardPaymentBase):
    """
    Visa card payment method.

    - Allows discounts up to 5% (modifier 0.95 to 1.0)
    - Awards 3% points on original price
    - Requires last 4 digits of card
    """

    min_modifier = Decimal("0.95")
    max_modifier = Decimal("1.0")
    points_rate = Decimal("0.03")


class MastercardPayment(CardPaymentBase):
    """
    Mastercard payment method.

    - Allows discounts up to 5% (modifier 0.95 to 1.0)
    - Awards 3% points on original price
    - Requires last 4 digits of card
    """

    min_modifier = Decimal("0.95")
    max_modifier = Decimal("1.0")
    points_rate = Decimal("0.03")


class AmexPayment(CardPaymentBase):
    """
    American Express (AMEX) payment method.

    AMEX has higher transaction fees, so:
    - Allows only 2% discount up to 1% surcharge (modifier 0.98 to 1.01)
    - Awards only 2% points on original price
    - Requires last 4 digits of card
    """

    min_modifier = Decimal("0.98")
    max_modifier = Decimal("1.01")
    points_rate = Decimal("0.02")


class JcbPayment(CardPaymentBase):
    """
    JCB card payment method.

    - Allows discounts up to 5% (modifier 0.95 to 1.0)
    - Awards 5% points on original price (highest among cards)
    - Requires last 4 digits of card
    """

    min_modifier = Decimal("0.95")
    max_modifier = Decimal("1.0")
    points_rate = Decimal("0.05")


class LinePayPayment(BasePaymentMethod):
    """
    LINE Pay mobile payment method.

    - No price modification allowed (modifier fixed at 1.0)
    - Awards 1% points on original price
    - No additional data required
    """

    min_modifier = Decimal("1.0")
    max_modifier = Decimal("1.0")
    points_rate = Decimal("0.01")

    def validate_additional_item(self, additional_item: Optional[dict]) -> dict:
        """LINE Pay doesn't require additional data."""
        return additional_item or {}


class PayPayPayment(BasePaymentMethod):
    """
    PayPay mobile payment method.

    - No price modification allowed (modifier fixed at 1.0)
    - Awards 1% points on original price
    - No additional data required
    """

    min_modifier = Decimal("1.0")
    max_modifier = Decimal("1.0")
    points_rate = Decimal("0.01")

    def validate_additional_item(self, additional_item: Optional[dict]) -> dict:
        """PayPay doesn't require additional data."""
        return additional_item or {}


class PointsPayment(BasePaymentMethod):
    """
    Points redemption payment method.

    When customers pay with their loyalty points:
    - No price modification allowed (modifier fixed at 1.0)
    - No new points awarded (0% points rate)
    - No additional data required
    """

    min_modifier = Decimal("1.0")
    max_modifier = Decimal("1.0")
    points_rate = Decimal("0.0")

    def validate_additional_item(self, additional_item: Optional[dict]) -> dict:
        """Points payment doesn't require additional data."""
        return additional_item or {}


class GrabPayPayment(BasePaymentMethod):
    """
    GrabPay mobile payment method.

    - No price modification allowed (modifier fixed at 1.0)
    - Awards 1% points on original price
    - No additional data required
    """

    min_modifier = Decimal("1.0")
    max_modifier = Decimal("1.0")
    points_rate = Decimal("0.01")

    def validate_additional_item(self, additional_item: Optional[dict]) -> dict:
        """GrabPay doesn't require additional data."""
        return additional_item or {}


class BankTransferPayment(BasePaymentMethod):
    """
    Bank transfer payment method.

    - No price modification allowed (modifier fixed at 1.0)
    - No points awarded (0% points rate)
    - Requires bank name and account number for record keeping
    """

    min_modifier = Decimal("1.0")
    max_modifier = Decimal("1.0")
    points_rate = Decimal("0.0")

    def validate_additional_item(self, additional_item: Optional[dict]) -> dict:
        """
        Validate bank transfer details.

        Args:
            additional_item: Must contain {"bank": "...", "account_number": "..."}

        Raises:
            PaymentMethodError: If bank or account_number is missing
        """
        if not additional_item:
            raise PaymentMethodError(
                "Bank transfer requires bank and account_number. "
                "Please provide them in additionalItem.",
                field="additionalItem"
            )

        if "bank" not in additional_item or not additional_item["bank"]:
            raise PaymentMethodError(
                "Bank transfer requires the bank name. "
                "Please provide 'bank' in additionalItem.",
                field="additionalItem.bank"
            )

        if "account_number" not in additional_item or not additional_item["account_number"]:
            raise PaymentMethodError(
                "Bank transfer requires the account number. "
                "Please provide 'account_number' in additionalItem.",
                field="additionalItem.account_number"
            )

        return {
            "bank": str(additional_item["bank"]).strip(),
            "account_number": str(additional_item["account_number"]).strip()
        }


class ChequePayment(BasePaymentMethod):
    """
    Cheque payment method.

    - Allows discounts up to 10% (modifier 0.9 to 1.0)
    - No points awarded (0% points rate)
    - Requires bank name and cheque number for verification
    """

    min_modifier = Decimal("0.9")
    max_modifier = Decimal("1.0")
    points_rate = Decimal("0.0")

    def validate_additional_item(self, additional_item: Optional[dict]) -> dict:
        """
        Validate cheque details.

        Args:
            additional_item: Must contain {"bank": "...", "cheque_number": "..."}

        Raises:
            PaymentMethodError: If bank or cheque_number is missing
        """
        if not additional_item:
            raise PaymentMethodError(
                "Cheque payment requires bank and cheque_number. "
                "Please provide them in additionalItem.",
                field="additionalItem"
            )

        if "bank" not in additional_item or not additional_item["bank"]:
            raise PaymentMethodError(
                "Cheque payment requires the bank name. "
                "Please provide 'bank' in additionalItem.",
                field="additionalItem.bank"
            )

        if "cheque_number" not in additional_item or not additional_item["cheque_number"]:
            raise PaymentMethodError(
                "Cheque payment requires the cheque number. "
                "Please provide 'cheque_number' in additionalItem.",
                field="additionalItem.cheque_number"
            )

        return {
            "bank": str(additional_item["bank"]).strip(),
            "cheque_number": str(additional_item["cheque_number"]).strip()
        }
