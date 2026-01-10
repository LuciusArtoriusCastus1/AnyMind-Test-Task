"""
Payment Method Factory

This module provides the factory for creating payment method strategy instances.
The factory pattern is used to:
1. Centralize payment method instantiation
2. Make it easy to add new payment methods
3. Provide a clean interface for the service layer

To add a new payment method:
1. Create a new class in methods.py inheriting from BasePaymentMethod
2. Add the new method to the PaymentMethod enum in models/payment.py
3. Register the method in PAYMENT_METHODS dict below
"""

from app.models.payment import PaymentMethod
from app.payment_methods.base import BasePaymentMethod, PaymentMethodError
from app.payment_methods.methods import (
    AmexPayment,
    BankTransferPayment,
    CashOnDeliveryPayment,
    CashPayment,
    ChequePayment,
    GrabPayPayment,
    JcbPayment,
    LinePayPayment,
    MastercardPayment,
    PayPayPayment,
    PointsPayment,
    VisaPayment,
)

# Registry mapping PaymentMethod enum values to their strategy classes
# This makes it trivial to add new payment methods - just add an entry here
PAYMENT_METHODS: dict[PaymentMethod, type[BasePaymentMethod]] = {
    PaymentMethod.CASH: CashPayment,
    PaymentMethod.CASH_ON_DELIVERY: CashOnDeliveryPayment,
    PaymentMethod.VISA: VisaPayment,
    PaymentMethod.MASTERCARD: MastercardPayment,
    PaymentMethod.AMEX: AmexPayment,
    PaymentMethod.JCB: JcbPayment,
    PaymentMethod.LINE_PAY: LinePayPayment,
    PaymentMethod.PAYPAY: PayPayPayment,
    PaymentMethod.POINTS: PointsPayment,
    PaymentMethod.GRAB_PAY: GrabPayPayment,
    PaymentMethod.BANK_TRANSFER: BankTransferPayment,
    PaymentMethod.CHEQUE: ChequePayment,
}


class PaymentMethodFactory:
    """
    Factory class for creating payment method strategy instances.

    This factory provides a centralized way to get the correct payment
    method handler based on the payment method enum value.

    Example:
        payment_handler = PaymentMethodFactory.create(PaymentMethod.VISA)
        final_price, points, data = payment_handler.process(
            price=Decimal("100.00"),
            price_modifier=Decimal("0.95"),
            additional_item={"last4": "1234"}
        )
    """

    @staticmethod
    def create(payment_method: PaymentMethod) -> BasePaymentMethod:
        """
        Create a payment method handler instance.

        Args:
            payment_method: The payment method enum value

        Returns:
            BasePaymentMethod: Instance of the appropriate payment handler

        Raises:
            PaymentMethodError: If the payment method is not supported
        """
        if payment_method not in PAYMENT_METHODS:
            raise PaymentMethodError(
                f"Unsupported payment method: {payment_method.value}. "
                f"Supported methods are: {', '.join(m.value for m in PAYMENT_METHODS)}",
                field="paymentMethod",
            )

        handler_class = PAYMENT_METHODS[payment_method]
        return handler_class()

    @staticmethod
    def get_supported_methods() -> list[str]:
        """
        Get list of supported payment method names.

        Returns:
            list[str]: List of payment method enum values
        """
        return [method.value for method in PAYMENT_METHODS]


def get_payment_method(payment_method: PaymentMethod) -> BasePaymentMethod:
    """
    Convenience function to get a payment method handler.

    This is a shortcut for PaymentMethodFactory.create() for simpler imports.

    Args:
        payment_method: The payment method enum value

    Returns:
        BasePaymentMethod: Instance of the appropriate payment handler
    """
    return PaymentMethodFactory.create(payment_method)
