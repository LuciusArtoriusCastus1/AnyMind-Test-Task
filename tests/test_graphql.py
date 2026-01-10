"""
Integration Tests for GraphQL API

Tests the complete GraphQL API including:
- Payment mutation with various payment methods
- Sales report query
- Error handling and validation

These tests use the full application stack with a test database.
"""


import pytest

pytestmark = pytest.mark.asyncio


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    async def test_health_check(self, test_client):
        """Test health check returns healthy status."""
        response = await test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestCreatePaymentMutation:
    """Tests for the createPayment GraphQL mutation."""

    async def test_create_payment_mastercard(self, test_client):
        """Test creating a payment with MASTERCARD."""
        mutation = """
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
        response = await test_client.post(
            "/graphql",
            json={"query": mutation}
        )
        assert response.status_code == 200
        data = response.json()

        assert "errors" not in data
        result = data["data"]["createPayment"]
        assert result["finalPrice"] == "95.00"
        assert result["points"] == 3  # 100 * 0.03

    async def test_create_payment_cash_on_delivery(self, test_client):
        """Test creating a payment with CASH_ON_DELIVERY."""
        mutation = """
            mutation {
                createPayment(input: {
                    customerId: "12345"
                    price: "100.00"
                    priceModifier: 1
                    paymentMethod: CASH_ON_DELIVERY
                    datetime: "2022-09-01T00:00:00Z"
                    additionalItem: { courier: "YAMATO" }
                }) {
                    ... on PaymentResponse {
                        finalPrice
                        points
                    }
                    ... on ErrorResponse {
                        error
                        message
                    }
                }
            }
        """
        response = await test_client.post(
            "/graphql",
            json={"query": mutation}
        )
        assert response.status_code == 200
        data = response.json()

        assert "errors" not in data
        result = data["data"]["createPayment"]
        assert result["finalPrice"] == "100.00"
        assert result["points"] == 5  # 100 * 0.05

    async def test_create_payment_cash(self, test_client):
        """Test creating a payment with CASH."""
        mutation = """
            mutation {
                createPayment(input: {
                    customerId: "customer123"
                    price: "200.00"
                    priceModifier: 0.9
                    paymentMethod: CASH
                    datetime: "2022-09-01T10:30:00Z"
                }) {
                    ... on PaymentResponse {
                        finalPrice
                        points
                    }
                }
            }
        """
        response = await test_client.post(
            "/graphql",
            json={"query": mutation}
        )
        assert response.status_code == 200
        data = response.json()

        result = data["data"]["createPayment"]
        assert result["finalPrice"] == "180.00"  # 200 * 0.9
        assert result["points"] == 10  # 200 * 0.05

    async def test_create_payment_invalid_price_modifier(self, test_client):
        """Test error when price modifier is out of range."""
        mutation = """
            mutation {
                createPayment(input: {
                    customerId: "12345"
                    price: "100.00"
                    priceModifier: 0.8
                    paymentMethod: CASH
                    datetime: "2022-09-01T00:00:00Z"
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
        response = await test_client.post(
            "/graphql",
            json={"query": mutation}
        )
        assert response.status_code == 200
        data = response.json()

        result = data["data"]["createPayment"]
        assert result["error"] == "VALIDATION_ERROR"
        assert "priceModifier" in result["field"]

    async def test_create_payment_missing_last4_for_card(self, test_client):
        """Test error when card payment is missing last4."""
        mutation = """
            mutation {
                createPayment(input: {
                    customerId: "12345"
                    price: "100.00"
                    priceModifier: 0.95
                    paymentMethod: VISA
                    datetime: "2022-09-01T00:00:00Z"
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
        response = await test_client.post(
            "/graphql",
            json={"query": mutation}
        )
        assert response.status_code == 200
        data = response.json()

        result = data["data"]["createPayment"]
        assert result["error"] == "VALIDATION_ERROR"
        assert "last4" in result["message"]

    async def test_create_payment_invalid_courier(self, test_client):
        """Test error when CASH_ON_DELIVERY has invalid courier."""
        mutation = """
            mutation {
                createPayment(input: {
                    customerId: "12345"
                    price: "100.00"
                    priceModifier: 1.0
                    paymentMethod: CASH_ON_DELIVERY
                    datetime: "2022-09-01T00:00:00Z"
                    additionalItem: { courier: "FEDEX" }
                }) {
                    ... on PaymentResponse {
                        finalPrice
                        points
                    }
                    ... on ErrorResponse {
                        error
                        message
                    }
                }
            }
        """
        response = await test_client.post(
            "/graphql",
            json={"query": mutation}
        )
        assert response.status_code == 200
        data = response.json()

        result = data["data"]["createPayment"]
        assert result["error"] == "VALIDATION_ERROR"
        assert "Invalid courier" in result["message"]

    async def test_create_payment_invalid_price_format(self, test_client):
        """Test error when price is not a valid number."""
        mutation = """
            mutation {
                createPayment(input: {
                    customerId: "12345"
                    price: "not_a_number"
                    priceModifier: 1.0
                    paymentMethod: CASH
                    datetime: "2022-09-01T00:00:00Z"
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
        response = await test_client.post(
            "/graphql",
            json={"query": mutation}
        )
        assert response.status_code == 200
        data = response.json()

        result = data["data"]["createPayment"]
        assert result["error"] == "VALIDATION_ERROR"
        assert "price" in result["field"]

    async def test_create_payment_bank_transfer(self, test_client):
        """Test creating a payment with BANK_TRANSFER."""
        mutation = """
            mutation {
                createPayment(input: {
                    customerId: "12345"
                    price: "500.00"
                    priceModifier: 1.0
                    paymentMethod: BANK_TRANSFER
                    datetime: "2022-09-01T00:00:00Z"
                    additionalItem: {
                        bank: "Kasikorn Bank"
                        accountNumber: "1234567890"
                    }
                }) {
                    ... on PaymentResponse {
                        finalPrice
                        points
                    }
                    ... on ErrorResponse {
                        error
                        message
                    }
                }
            }
        """
        response = await test_client.post(
            "/graphql",
            json={"query": mutation}
        )
        assert response.status_code == 200
        data = response.json()

        result = data["data"]["createPayment"]
        assert result["finalPrice"] == "500.00"
        assert result["points"] == 0  # BANK_TRANSFER gives no points

    async def test_create_payment_cheque(self, test_client):
        """Test creating a payment with CHEQUE."""
        mutation = """
            mutation {
                createPayment(input: {
                    customerId: "12345"
                    price: "1000.00"
                    priceModifier: 0.95
                    paymentMethod: CHEQUE
                    datetime: "2022-09-01T00:00:00Z"
                    additionalItem: {
                        bank: "Bangkok Bank"
                        chequeNumber: "CH123456789"
                    }
                }) {
                    ... on PaymentResponse {
                        finalPrice
                        points
                    }
                    ... on ErrorResponse {
                        error
                        message
                    }
                }
            }
        """
        response = await test_client.post(
            "/graphql",
            json={"query": mutation}
        )
        assert response.status_code == 200
        data = response.json()

        result = data["data"]["createPayment"]
        assert result["finalPrice"] == "950.00"
        assert result["points"] == 0


class TestSalesReportQuery:
    """Tests for the salesReport GraphQL query."""

    async def test_sales_report_with_data(self, test_client, sample_payments):
        """Test sales report returns aggregated data."""
        query = """
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
        """
        response = await test_client.post(
            "/graphql",
            json={"query": query}
        )
        assert response.status_code == 200
        data = response.json()

        result = data["data"]["salesReport"]
        assert "sales" in result
        assert len(result["sales"]) > 0

    async def test_sales_report_empty_range(self, test_client):
        """Test sales report with no data in range."""
        query = """
            query {
                salesReport(input: {
                    startDatetime: "2020-01-01T00:00:00Z"
                    endDatetime: "2020-01-01T23:59:59Z"
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
        """
        response = await test_client.post(
            "/graphql",
            json={"query": query}
        )
        assert response.status_code == 200
        data = response.json()

        result = data["data"]["salesReport"]
        assert result["sales"] == []

    async def test_sales_report_invalid_range(self, test_client):
        """Test error when end datetime is before start."""
        query = """
            query {
                salesReport(input: {
                    startDatetime: "2022-09-02T00:00:00Z"
                    endDatetime: "2022-09-01T00:00:00Z"
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
        """
        response = await test_client.post(
            "/graphql",
            json={"query": query}
        )
        assert response.status_code == 200
        data = response.json()

        result = data["data"]["salesReport"]
        assert result["error"] == "VALIDATION_ERROR"


class TestSupportedPaymentMethodsQuery:
    """Tests for the supportedPaymentMethods query."""

    async def test_get_supported_methods(self, test_client):
        """Test listing all supported payment methods."""
        query = """
            query {
                supportedPaymentMethods
            }
        """
        response = await test_client.post(
            "/graphql",
            json={"query": query}
        )
        assert response.status_code == 200
        data = response.json()

        methods = data["data"]["supportedPaymentMethods"]
        assert "CASH" in methods
        assert "VISA" in methods
        assert "MASTERCARD" in methods
        assert "CASH_ON_DELIVERY" in methods
        assert len(methods) == 12  # All 12 payment methods
