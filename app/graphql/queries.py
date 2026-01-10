"""
GraphQL Queries

This module defines GraphQL queries for the payment system.
Contains the sales report query for retrieving hourly sales data.

Queries in GraphQL represent read-only operations that fetch data
without modifying the database state.
"""

import strawberry
from strawberry.types import Info

from app.graphql.types import (
    ErrorResponse,
    HourlySales,
    PaymentMethodEnum,
    SalesReportInput,
    SalesReportResponse,
    SalesReportResult,
)
from app.payment_methods.factory import PaymentMethodFactory
from app.services.payment_service import PaymentService, PaymentServiceError


@strawberry.type
class Query:
    """
    GraphQL Query type containing all query operations.

    Currently, supports:
    - salesReport: Get hourly sales data within a date range
    - supportedPaymentMethods: List all available payment methods
    """

    @strawberry.field(description="Get hourly sales report within a date range")
    async def sales_report(
        self,
        info: Info,
        input: SalesReportInput,
    ) -> SalesReportResult:
        """
        Retrieve aggregated sales data broken down by hour.

        This query aggregates all payment transactions within the specified
        date range, grouping them by hour and summing the sales amounts
        and points.

        Args:
            info: Strawberry context containing the database session
            input: Date range for the report

        Returns:
            SalesReportResult: Either SalesReportResponse or ErrorResponse

        Example GraphQL query:
            query {
                salesReport(input: {
                    startDatetime: "2022-09-01T00:00:00Z"
                    endDatetime: "2022-09-01T23:59:59Z"
                }) {
                    ... on SalesReportResponse {
                        sales {
                            datetime
                            sales
                            points
                        }
                    }
                    ... on ErrorResponse {
                        error
                        message
                    }
                }
            }

        Response example:
            {
                "sales": [
                    {
                        "datetime": "2022-09-01T00:00:00Z",
                        "sales": "1000.00",
                        "points": 10
                    },
                    {
                        "datetime": "2022-09-01T01:00:00Z",
                        "sales": "2000.00",
                        "points": 20
                    }
                ]
            }
        """
        db = info.context["db"]

        service = PaymentService(db)

        try:
            report_data = await service.get_sales_report(
                start_datetime=input.start_datetime,
                end_datetime=input.end_datetime,
            )

            hourly_sales = [
                HourlySales(
                    datetime=item["datetime"],
                    sales=item["sales"],
                    points=item["points"],
                )
                for item in report_data
            ]

            return SalesReportResponse(sales=hourly_sales)

        except PaymentServiceError as e:
            return ErrorResponse(
                error="VALIDATION_ERROR",
                message=e.message,
                field=e.field,
            )
        except Exception:
            return ErrorResponse(
                error="INTERNAL_ERROR",
                message="An unexpected error occurred while generating the report",
                field=None,
            )

    @strawberry.field(description="List all supported payment methods")
    def supported_payment_methods(self) -> list[PaymentMethodEnum]:
        """
        Get a list of all supported payment methods.

        This is useful for clients to know which payment methods
        are available in the system.

        Returns:
            List[PaymentMethodEnum]: All available payment methods
        """
        method_names = PaymentMethodFactory.get_supported_methods()
        return [PaymentMethodEnum(name) for name in method_names]
