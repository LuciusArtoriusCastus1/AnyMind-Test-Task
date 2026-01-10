"""
Payment Service - Business Logic Layer

This module contains the core business logic for payment processing and sales reporting.
It orchestrates between the database layer and payment method strategies.

Responsibilities:
- Process payment requests with validation
- Store payment records in the database
- Generate hourly sales reports within date ranges

Design Decisions:
1. Async operations for scalability under concurrent requests
2. Decimal precision for all monetary calculations
3. Hourly aggregation for sales reports using SQL window functions
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentMethod
from app.payment_methods import get_payment_method
from app.payment_methods.base import PaymentMethodError


class PaymentServiceError(Exception):
    """
    Service-level exception for payment processing errors.

    Wraps lower-level errors with additional context for the API layer.
    """

    def __init__(self, message: str, field: str | None = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class PaymentService:
    """
    Service class for payment operations.

    This class provides the main interface for:
    1. Processing payments (validation, calculation, storage)
    2. Querying sales reports by date range

    All operations are async for optimal performance under load.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the payment service.

        Args:
            db: Async database session for database operations
        """
        self.db = db

    async def process_payment(
        self,
        customer_id: str,
        price: str,
        price_modifier: float,
        payment_method: str,
        transaction_datetime: datetime,
        additional_item: dict | None = None,
    ) -> dict:
        """
        Process a payment transaction.

        This method:
        1. Validates all input data
        2. Applies the appropriate payment method strategy
        3. Calculates final price and points
        4. Stores the transaction in the database

        Args:
            customer_id: Unique identifier for the customer
            price: Original price as string (e.g., "100.00")
            price_modifier: Price modifier to apply (e.g., 0.95 for 5% off)
            payment_method: Payment method name (e.g., "VISA")
            transaction_datetime: When the payment was made
            additional_item: Payment-specific additional data

        Returns:
            dict: {
                "final_price": "95.00",  # Calculated final price
                "points": 3               # Loyalty points awarded
            }

        Raises:
            PaymentServiceError: If validation fails or processing errors occur
        """
        if not customer_id or not customer_id.strip():
            raise PaymentServiceError(
                "Customer ID is required",
                field="customerId"
            )

        try:
            price_decimal = Decimal(price)
            if price_decimal <= 0:
                raise PaymentServiceError(
                    "Price must be greater than zero",
                    field="price"
                )
        except (InvalidOperation, ValueError):
            raise PaymentServiceError(
                f"Invalid price format: {price}. Must be a valid decimal number.",
                field="price"
            ) from None

        try:
            modifier_decimal = Decimal(str(price_modifier))
        except (InvalidOperation, ValueError):
            raise PaymentServiceError(
                f"Invalid price modifier: {price_modifier}",
                field="priceModifier"
            ) from None

        try:
            payment_method_enum = PaymentMethod(payment_method)
        except ValueError:
            valid_methods = [m.value for m in PaymentMethod]
            raise PaymentServiceError(
                f"Invalid payment method: {payment_method}. "
                f"Valid methods are: {', '.join(valid_methods)}",
                field="paymentMethod"
            ) from None

        try:
            handler = get_payment_method(payment_method_enum)
            final_price, points, validated_additional_item = handler.process(
                price=price_decimal,
                price_modifier=modifier_decimal,
                additional_item=additional_item
            )
        except PaymentMethodError as e:
            raise PaymentServiceError(e.message, e.field) from None

        payment = Payment(
            customer_id=customer_id.strip(),
            price=price_decimal,
            price_modifier=modifier_decimal,
            final_price=final_price,
            points=points,
            payment_method=payment_method_enum,
            additional_item=validated_additional_item,
            datetime=transaction_datetime,
        )

        self.db.add(payment)
        await self.db.flush()

        return {
            "final_price": str(final_price),
            "points": points
        }

    async def get_sales_report(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> list[dict]:
        """
        Get hourly sales report within a date range.

        Aggregates all payments within the specified range, grouped by hour.
        Returns sales totals and points for each hour that had transactions.

        Args:
            start_datetime: Start of the date range (inclusive)
            end_datetime: End of the date range (inclusive)

        Returns:
            List[dict]: List of hourly sales data, each containing:
                - datetime: ISO format string of the hour
                - sales: Total sales amount for that hour
                - points: Total points awarded that hour

        Raises:
            PaymentServiceError: If date range is invalid
        """
        if start_datetime >= end_datetime:
            raise PaymentServiceError(
                "Start datetime must be before end datetime",
                field="startDateTime"
            )

        hour_trunc = func.date_trunc("hour", Payment.datetime)

        query = (
            select(
                hour_trunc.label("hour"),
                func.sum(Payment.final_price).label("total_sales"),
                func.sum(Payment.points).label("total_points"),
            )
            .where(Payment.datetime >= start_datetime)
            .where(Payment.datetime <= end_datetime)
            .group_by(hour_trunc)
            .order_by(hour_trunc)
        )

        result = await self.db.execute(query)
        rows = result.all()

        sales_report = []
        for row in rows:
            sales_report.append({
                "datetime": row.hour.isoformat().replace("+00:00", "Z"),
                "sales": f"{row.total_sales:.2f}",
                "points": int(row.total_points),
            })

        return sales_report
