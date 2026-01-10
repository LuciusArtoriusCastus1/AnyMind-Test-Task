"""
Unit Tests for Payment Methods

Tests the payment method strategy classes for:
- Price modifier validation
- Points calculation
- Additional item validation
- Final price calculation

Each payment method is tested with valid and invalid inputs.
"""

from decimal import Decimal

import pytest

from app.models.payment import PaymentMethod
from app.payment_methods.base import PaymentMethodError
from app.payment_methods.factory import get_payment_method
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


class TestCashPayment:
    """Tests for CASH payment method."""

    def test_valid_price_modifier_minimum(self):
        """Test minimum allowed price modifier (0.9)."""
        handler = CashPayment()
        final_price, points, additional = handler.process(
            price=Decimal("100.00"), price_modifier=Decimal("0.9"), additional_item=None
        )
        assert final_price == Decimal("90.00")
        assert points == 5  # 100 * 0.05 = 5

    def test_valid_price_modifier_maximum(self):
        """Test maximum allowed price modifier (1.0)."""
        handler = CashPayment()
        final_price, points, additional = handler.process(
            price=Decimal("100.00"), price_modifier=Decimal("1.0"), additional_item=None
        )
        assert final_price == Decimal("100.00")
        assert points == 5

    def test_invalid_price_modifier_too_low(self):
        """Test price modifier below minimum."""
        handler = CashPayment()
        with pytest.raises(PaymentMethodError) as exc_info:
            handler.process(
                price=Decimal("100.00"), price_modifier=Decimal("0.89"), additional_item=None
            )
        assert "priceModifier" in exc_info.value.field

    def test_invalid_price_modifier_too_high(self):
        """Test price modifier above maximum."""
        handler = CashPayment()
        with pytest.raises(PaymentMethodError) as exc_info:
            handler.process(
                price=Decimal("100.00"), price_modifier=Decimal("1.01"), additional_item=None
            )
        assert "priceModifier" in exc_info.value.field

    def test_points_calculation(self):
        """Test points are calculated from original price."""
        handler = CashPayment()
        final_price, points, _ = handler.process(
            price=Decimal("200.00"), price_modifier=Decimal("0.9"), additional_item=None
        )
        # Points from original price: 200 * 0.05 = 10
        assert points == 10
        # Final price with discount: 200 * 0.9 = 180
        assert final_price == Decimal("180.00")


class TestCashOnDeliveryPayment:
    """Tests for CASH_ON_DELIVERY payment method."""

    def test_valid_courier_yamato(self):
        """Test valid YAMATO courier."""
        handler = CashOnDeliveryPayment()
        final_price, points, additional = handler.process(
            price=Decimal("100.00"),
            price_modifier=Decimal("1.0"),
            additional_item={"courier": "YAMATO"},
        )
        assert final_price == Decimal("100.00")
        assert points == 5
        assert additional["courier"] == "YAMATO"

    def test_valid_courier_sagawa(self):
        """Test valid SAGAWA courier."""
        handler = CashOnDeliveryPayment()
        _, _, additional = handler.process(
            price=Decimal("100.00"),
            price_modifier=Decimal("1.02"),
            additional_item={"courier": "SAGAWA"},
        )
        assert additional["courier"] == "SAGAWA"

    def test_courier_case_insensitive(self):
        """Test courier name is normalized to uppercase."""
        handler = CashOnDeliveryPayment()
        _, _, additional = handler.process(
            price=Decimal("100.00"),
            price_modifier=Decimal("1.0"),
            additional_item={"courier": "yamato"},
        )
        assert additional["courier"] == "YAMATO"

    def test_missing_courier(self):
        """Test error when courier is missing."""
        handler = CashOnDeliveryPayment()
        with pytest.raises(PaymentMethodError) as exc_info:
            handler.process(
                price=Decimal("100.00"), price_modifier=Decimal("1.0"), additional_item={}
            )
        assert "courier" in exc_info.value.message

    def test_invalid_courier(self):
        """Test error with invalid courier name."""
        handler = CashOnDeliveryPayment()
        with pytest.raises(PaymentMethodError) as exc_info:
            handler.process(
                price=Decimal("100.00"),
                price_modifier=Decimal("1.0"),
                additional_item={"courier": "FEDEX"},
            )
        assert "Invalid courier" in exc_info.value.message

    def test_price_modifier_with_surcharge(self):
        """Test maximum 2% surcharge."""
        handler = CashOnDeliveryPayment()
        final_price, _, _ = handler.process(
            price=Decimal("100.00"),
            price_modifier=Decimal("1.02"),
            additional_item={"courier": "YAMATO"},
        )
        assert final_price == Decimal("102.00")


class TestCardPayments:
    """Tests for card payment methods (VISA, MASTERCARD, AMEX, JCB)."""

    @pytest.mark.parametrize(
        "handler_class,min_mod,max_mod,points_rate",
        [
            (VisaPayment, "0.95", "1.0", 3),
            (MastercardPayment, "0.95", "1.0", 3),
            (AmexPayment, "0.98", "1.01", 2),
            (JcbPayment, "0.95", "1.0", 5),
        ],
    )
    def test_valid_card_payment(self, handler_class, min_mod, max_mod, points_rate):
        """Test valid card payment with last4 digits."""
        handler = handler_class()
        final_price, points, additional = handler.process(
            price=Decimal("100.00"),
            price_modifier=Decimal(min_mod),
            additional_item={"last4": "1234"},
        )
        expected_price = Decimal("100.00") * Decimal(min_mod)
        assert final_price == expected_price.quantize(Decimal("0.01"))
        assert points == points_rate  # 100 * rate
        assert additional["last4"] == "1234"

    def test_missing_last4(self):
        """Test error when last4 is missing."""
        handler = VisaPayment()
        with pytest.raises(PaymentMethodError) as exc_info:
            handler.process(
                price=Decimal("100.00"), price_modifier=Decimal("0.95"), additional_item={}
            )
        assert "last4" in exc_info.value.message

    def test_invalid_last4_not_digits(self):
        """Test error when last4 contains non-digits."""
        handler = VisaPayment()
        with pytest.raises(PaymentMethodError) as exc_info:
            handler.process(
                price=Decimal("100.00"),
                price_modifier=Decimal("0.95"),
                additional_item={"last4": "12ab"},
            )
        assert "Invalid card last4" in exc_info.value.message

    def test_invalid_last4_wrong_length(self):
        """Test error when last4 is not exactly 4 digits."""
        handler = VisaPayment()
        with pytest.raises(PaymentMethodError) as exc_info:
            handler.process(
                price=Decimal("100.00"),
                price_modifier=Decimal("0.95"),
                additional_item={"last4": "123"},
            )
        assert "exactly 4 digits" in exc_info.value.message

    def test_amex_allows_surcharge(self):
        """Test AMEX allows up to 1% surcharge."""
        handler = AmexPayment()
        final_price, _, _ = handler.process(
            price=Decimal("100.00"),
            price_modifier=Decimal("1.01"),
            additional_item={"last4": "1234"},
        )
        assert final_price == Decimal("101.00")


class TestDigitalPayments:
    """Tests for digital payment methods (LINE_PAY, PAYPAY, GRAB_PAY, POINTS)."""

    @pytest.mark.parametrize(
        "handler_class,points_rate",
        [
            (LinePayPayment, 1),
            (PayPayPayment, 1),
            (GrabPayPayment, 1),
            (PointsPayment, 0),
        ],
    )
    def test_no_price_modification(self, handler_class, points_rate):
        """Test digital payments don't allow price modification."""
        handler = handler_class()
        final_price, points, _ = handler.process(
            price=Decimal("100.00"), price_modifier=Decimal("1.0"), additional_item=None
        )
        assert final_price == Decimal("100.00")
        assert points == points_rate

    def test_digital_payment_modifier_must_be_one(self):
        """Test digital payments reject modifier != 1.0."""
        handler = LinePayPayment()
        with pytest.raises(PaymentMethodError):
            handler.process(
                price=Decimal("100.00"), price_modifier=Decimal("0.99"), additional_item=None
            )


class TestBankTransferPayment:
    """Tests for BANK_TRANSFER payment method."""

    def test_valid_bank_transfer(self):
        """Test valid bank transfer with all required fields."""
        handler = BankTransferPayment()
        final_price, points, additional = handler.process(
            price=Decimal("100.00"),
            price_modifier=Decimal("1.0"),
            additional_item={"bank": "Kasikorn", "account_number": "1234567890"},
        )
        assert final_price == Decimal("100.00")
        assert points == 0
        assert additional["bank"] == "Kasikorn"
        assert additional["account_number"] == "1234567890"

    def test_missing_bank(self):
        """Test error when bank is missing."""
        handler = BankTransferPayment()
        with pytest.raises(PaymentMethodError) as exc_info:
            handler.process(
                price=Decimal("100.00"),
                price_modifier=Decimal("1.0"),
                additional_item={"account_number": "1234567890"},
            )
        assert "bank" in exc_info.value.message

    def test_missing_account_number(self):
        """Test error when account_number is missing."""
        handler = BankTransferPayment()
        with pytest.raises(PaymentMethodError) as exc_info:
            handler.process(
                price=Decimal("100.00"),
                price_modifier=Decimal("1.0"),
                additional_item={"bank": "Kasikorn"},
            )
        assert "account_number" in exc_info.value.message


class TestChequePayment:
    """Tests for CHEQUE payment method."""

    def test_valid_cheque(self):
        """Test valid cheque payment with all required fields."""
        handler = ChequePayment()
        final_price, points, additional = handler.process(
            price=Decimal("100.00"),
            price_modifier=Decimal("0.9"),
            additional_item={"bank": "Bangkok Bank", "cheque_number": "CH123456"},
        )
        assert final_price == Decimal("90.00")
        assert points == 0
        assert additional["bank"] == "Bangkok Bank"
        assert additional["cheque_number"] == "CH123456"

    def test_missing_cheque_number(self):
        """Test error when cheque_number is missing."""
        handler = ChequePayment()
        with pytest.raises(PaymentMethodError) as exc_info:
            handler.process(
                price=Decimal("100.00"),
                price_modifier=Decimal("1.0"),
                additional_item={"bank": "Bangkok Bank"},
            )
        assert "cheque_number" in exc_info.value.message


class TestPaymentMethodFactory:
    """Tests for the payment method factory."""

    @pytest.mark.parametrize("payment_method", list(PaymentMethod))
    def test_factory_creates_all_methods(self, payment_method):
        """Test factory can create handler for each payment method."""
        handler = get_payment_method(payment_method)
        assert handler is not None

    def test_factory_returns_correct_type(self):
        """Test factory returns correct handler type."""
        handler = get_payment_method(PaymentMethod.VISA)
        assert isinstance(handler, VisaPayment)
