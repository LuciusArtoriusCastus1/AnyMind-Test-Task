"""
GraphQL Mutations

This module defines GraphQL mutations for the payment system.
Currently, contains the payment processing mutation.

Mutations in GraphQL represent operations that modify data.
In this case, processing a payment creates a new payment record.
"""

import strawberry
from strawberry.types import Info

from app.graphql.types import (
    ErrorResponse,
    PaymentInput,
    PaymentResponse,
    PaymentResult,
)
from app.services.payment_service import PaymentService, PaymentServiceError


def convert_additional_item_to_dict(additional_item) -> dict | None:
    """
    Convert Strawberry input type to dictionary for the service layer.

    Filters out None values so only provided fields are passed through.

    Args:
        additional_item: AdditionalItemInput instance or None

    Returns:
        dict: Dictionary with non-None fields, or None if input is None
    """
    if additional_item is None:
        return None

    result = {}
    if additional_item.last4 is not None:
        result["last4"] = additional_item.last4
    if additional_item.courier is not None:
        result["courier"] = additional_item.courier
    if additional_item.bank is not None:
        result["bank"] = additional_item.bank
    if additional_item.account_number is not None:
        result["account_number"] = additional_item.account_number
    if additional_item.cheque_number is not None:
        result["cheque_number"] = additional_item.cheque_number

    return result if result else None


@strawberry.type
class Mutation:
    """
    GraphQL Mutation type containing all mutation operations.

    Currently, supports:
    - createPayment: Process a payment transaction
    """

    @strawberry.mutation(description="Process a payment transaction")
    async def create_payment(
        self,
        info: Info,
        input: PaymentInput,
    ) -> PaymentResult:
        """
        Process a payment and return the final price and points.

        This mutation:
        1. Validates all input data
        2. Verifies the price modifier is within the allowed range for the payment method
        3. Validates additional payment-specific data
        4. Calculates final price and loyalty points
        5. Stores the transaction in the database

        Args:
            info: Strawberry context containing the database session
            input: Payment input data

        Returns:
            PaymentResult: Either PaymentResponse on success or ErrorResponse on failure

        Example GraphQL mutation:
            mutation {
                createPayment(input: {
                    customerId: "12345"
                    price: "100.00"
                    priceModifier: 0.95
                    paymentMethod: MASTERCARD
                    datetime: "2022-09-01T00:00:00Z"
                    additionalItem: { last4: "1234" }
                }) {
                    ... on PaymentResponse {
                        finalPrice
                        points
                    }
                    ... on ErrorResponse {
                        error
                        message
                        field
                    }
                }
            }
        """
        db = info.context["db"]

        service = PaymentService(db)

        try:
            additional_item_dict = convert_additional_item_to_dict(input.additional_item)

            result = await service.process_payment(
                customer_id=input.customer_id,
                price=input.price,
                price_modifier=input.price_modifier,
                payment_method=input.payment_method.value,
                transaction_datetime=input.datetime,
                additional_item=additional_item_dict,
            )

            return PaymentResponse(
                final_price=result["final_price"],
                points=result["points"],
            )

        except PaymentServiceError as e:
            return ErrorResponse(
                error="VALIDATION_ERROR",
                message=e.message,
                field=e.field,
            )
        except Exception:
            return ErrorResponse(
                error="INTERNAL_ERROR",
                message="An unexpected error occurred while processing the payment",
                field=None,
            )
