# AnyMind POS Payment System

A FastAPI + GraphQL backend system for processing e-commerce payments with multiple payment methods, dynamic pricing modifiers, and loyalty points calculation.

## Features

- **Multiple Payment Methods**: Support for 12 different payment methods including credit cards (VISA, Mastercard, AMEX, JCB), cash, digital wallets (LINE Pay, PayPay, GrabPay), and more
- **Dynamic Price Modifiers**: Each payment method has configurable price modifier ranges for discounts or surcharges
- **Loyalty Points System**: Automatic points calculation based on payment method
- **Sales Reporting**: Hourly aggregated sales data within date ranges
- **GraphQL API**: Modern API with interactive playground
- **PostgreSQL Database**: Robust data persistence
- **Docker Support**: Easy deployment with Docker Compose
- **Comprehensive Tests**: Unit and integration tests with PostgreSQL

## Payment Methods Overview

| Payment Method | Price Modifier Range | Points Rate | Additional Data Required |
|---------------|---------------------|-------------|-------------------------|
| CASH | 0.9 - 1.0 | 5% | None |
| CASH_ON_DELIVERY | 1.0 - 1.02 | 5% | courier (YAMATO/SAGAWA) |
| VISA | 0.95 - 1.0 | 3% | last4 digits |
| MASTERCARD | 0.95 - 1.0 | 3% | last4 digits |
| AMEX | 0.98 - 1.01 | 2% | last4 digits |
| JCB | 0.95 - 1.0 | 5% | last4 digits |
| LINE_PAY | 1.0 | 1% | None |
| PAYPAY | 1.0 | 1% | None |
| POINTS | 1.0 | 0% | None |
| GRAB_PAY | 1.0 | 1% | None |
| BANK_TRANSFER | 1.0 | 0% | bank, account_number |
| CHEQUE | 0.9 - 1.0 | 0% | bank, cheque_number |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd AnyMind-Test-Task
```

2. Start the services:
```bash
docker-compose up -d
```

3. Access the GraphQL playground at http://localhost:8000/graphql

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Start PostgreSQL (using Docker):
```bash
docker run -d --name postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=anymind_pos \
  -p 5432:5432 \
  postgres:15-alpine
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

6. Access the GraphQL playground at http://localhost:8000/graphql

## API Usage

### GraphQL Endpoint

- **URL**: `POST /graphql`
- **Playground**: `GET /graphql`

### Create Payment Mutation

```graphql
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
```

**Response:**
```json
{
  "data": {
    "createPayment": {
      "finalPrice": "95.00",
      "points": 3
    }
  }
}
```

### Sales Report Query

```graphql
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
```

**Response:**
```json
{
  "data": {
    "salesReport": {
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
  }
}
```

### List Supported Payment Methods

```graphql
query {
  supportedPaymentMethods
}
```

## Running Tests

Tests use a separate PostgreSQL database to ensure full compatibility with production.

```bash
# Start the test database
docker-compose -f tests/docker-compose.test.yml up -d

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing --cov-report=html -v

# Run specific test file
pytest tests/test_payment_methods.py -v

# Stop the test database
docker-compose -f tests/docker-compose.test.yml down -v
```

## Linting

The project uses [Ruff](https://github.com/astral-sh/ruff) for linting and code formatting.

```bash
# Check for linting issues
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code
ruff format .
```

## Project Structure

```
AnyMind-Test-Task/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection management
│   ├── models/
│   │   ├── __init__.py
│   │   └── payment.py       # SQLAlchemy Payment model
│   ├── services/
│   │   ├── __init__.py
│   │   └── payment_service.py   # Business logic
│   ├── payment_methods/
│   │   ├── __init__.py
│   │   ├── base.py          # Base strategy class
│   │   ├── methods.py       # Payment method implementations
│   │   └── factory.py       # Factory for creating handlers
│   └── graphql/
│       ├── __init__.py
│       ├── types.py         # GraphQL type definitions
│       ├── queries.py       # GraphQL queries
│       └── mutations.py     # GraphQL mutations
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures
│   ├── docker-compose.test.yml  # Test database setup
│   ├── test_payment_methods.py  # Unit tests
│   └── test_graphql.py          # Integration tests
├── alembic/                 # Database migrations
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml           # Project config and linting rules
├── requirements.txt
├── .env.example
└── README.md
```

## Architecture

### Design Patterns

1. **Strategy Pattern**: Each payment method is a separate strategy class implementing a common interface. This makes it easy to add new payment methods.

2. **Factory Pattern**: `PaymentMethodFactory` creates the appropriate payment handler based on the payment method enum.

3. **Repository Pattern**: The service layer handles all database operations, keeping business logic separate from data access.

### Scalability Considerations

- **Connection Pooling**: SQLAlchemy async engine with configurable pool size
- **Async Operations**: All database operations are async for better concurrency
- **Stateless API**: Application is stateless, allowing horizontal scaling
- **Database Indexes**: Optimized indexes for common query patterns

## Adding a New Payment Method

To add a new payment method, follow these steps:

### 1. Add to the enum in `app/models/payment.py`:
```python
class PaymentMethod(str, enum.Enum):
    # ... existing methods ...
    APPLE_PAY = "APPLE_PAY"  # Add new method
```

### 2. Create handler class in `app/payment_methods/methods.py`:
```python
class ApplePayPayment(BasePaymentMethod):
    """Apple Pay payment method."""

    min_modifier = Decimal("1.0")
    max_modifier = Decimal("1.0")
    points_rate = Decimal("0.01")

    def validate_additional_item(self, additional_item: dict | None) -> dict:
        return additional_item or {}
```

### 3. Register in `app/payment_methods/factory.py`:
```python
from app.payment_methods.methods import ApplePayPayment

PAYMENT_METHODS[PaymentMethod.APPLE_PAY] = ApplePayPayment
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "app": "AnyMind POS Payment System",
  "version": "1.0.0"
}
```
