"""
GraphQL Type Definitions

This module defines all GraphQL types using Strawberry's type system.
Strawberry uses Python type hints and dataclasses to define the schema.

Types are organized into:
1. Enums - Payment methods
2. Input Types - Request structures for mutations/queries
3. Output Types - Response structures
4. Error Types - Structured error responses

Design Philosophy:
- Use Optional for truly optional fields
- Use explicit types for better documentation
- Include descriptions for all types and fields
"""

from datetime import datetime
from enum import Enum

import strawberry

# ============================================================================
# Enums
# ============================================================================


@strawberry.enum(description="Available payment methods in the system")
class PaymentMethodEnum(Enum):
    """
    Enumeration of all supported payment methods.

    Each method has different price modifier ranges and points rates:
    - CASH: Up to 10% discount, 5% points
    - CASH_ON_DELIVERY: Up to 2% surcharge, 5% points
    - VISA/MASTERCARD: Up to 5% discount, 3% points
    - AMEX: 2% discount to 1% surcharge, 2% points
    - JCB: Up to 5% discount, 5% points
    - LINE_PAY/PAYPAY/GRAB_PAY: No modifier, 1% points
    - POINTS: No modifier, no points (redemption)
    - BANK_TRANSFER: No modifier, no points
    - CHEQUE: Up to 10% discount, no points
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


# ============================================================================
# Input Types
# ============================================================================


@strawberry.input(description="Additional payment-specific information")
class AdditionalItemInput:
    """
    Additional data required by certain payment methods.

    Fields are optional because different payment methods need different data:
    - Card payments (VISA, MASTERCARD, AMEX, JCB): Require last4
    - CASH_ON_DELIVERY: Requires courier
    - BANK_TRANSFER: Requires bank and account_number
    - CHEQUE: Requires bank and cheque_number
    """

    last4: str | None = None
    courier: str | None = None
    bank: str | None = None
    account_number: str | None = None
    cheque_number: str | None = None


@strawberry.input(description="Input for processing a payment")
class PaymentInput:
    """
    Request structure for the payment mutation.

    This matches the API specification:
    {
        "customerId": "12345",
        "price": "100.00",
        "priceModifier": 0.95,
        "paymentMethod": "MASTERCARD",
        "datetime": "2022-09-01T00:00:00Z",
        "additionalItem": { "last4": "1234" }
    }
    """

    customer_id: str
    price: str
    price_modifier: float
    payment_method: PaymentMethodEnum
    datetime: datetime
    additional_item: AdditionalItemInput | None = None


@strawberry.input(description="Input for querying sales report")
class SalesReportInput:
    """
    Request structure for the sales report query.

    Specifies a date range for aggregating hourly sales data.
    """

    start_datetime: datetime
    end_datetime: datetime


# ============================================================================
# Output Types
# ============================================================================


@strawberry.type(description="Response for a successful payment")
class PaymentResponse:
    """
    Response structure for successful payment processing.

    Matches the API specification:
    {
        "finalPrice": "95.00",
        "points": 3
    }
    """

    final_price: str = strawberry.field(description="Final price after applying the price modifier")
    points: int = strawberry.field(description="Loyalty points awarded for this transaction")


@strawberry.type(description="Hourly sales data")
class HourlySales:
    """
    Aggregated sales data for a single hour.

    Part of the sales report response.
    """

    datetime: str = strawberry.field(description="Hour boundary in ISO 8601 format")
    sales: str = strawberry.field(description="Total sales amount for this hour")
    points: int = strawberry.field(description="Total points awarded during this hour")


@strawberry.type(description="Sales report response")
class SalesReportResponse:
    """
    Response structure for sales report query.

    Contains a list of hourly sales data within the requested date range.
    """

    sales: list[HourlySales] = strawberry.field(description="List of hourly sales data")


# ============================================================================
# Error Types
# ============================================================================


@strawberry.type(description="Error response")
class ErrorResponse:
    """
    Structured error response matching the API specification.

    Provides clear error messages and field-level information
    to help clients understand and fix issues.
    """

    error: str = strawberry.field(description="Error type or code")
    message: str = strawberry.field(description="Human-readable error description")
    field: str | None = strawberry.field(
        default=None, description="The specific field that caused the error"
    )


PaymentResult = strawberry.union(
    "PaymentResult",
    types=[PaymentResponse, ErrorResponse],
    description="Result of a payment operation - either success or error",
)

SalesReportResult = strawberry.union(
    "SalesReportResult",
    types=[SalesReportResponse, ErrorResponse],
    description="Result of a sales report query - either data or error",
)
