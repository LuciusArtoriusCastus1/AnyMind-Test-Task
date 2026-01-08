"""
GraphQL Schema Definition

This module combines queries and mutations into the final GraphQL schema.
The schema is used by the Strawberry FastAPI integration to handle
GraphQL requests.

Schema Structure:
- Query: Read operations (salesReport, supportedPaymentMethods)
- Mutation: Write operations (createPayment)
"""

import strawberry

from app.graphql.queries import Query
from app.graphql.mutations import Mutation


# Create the GraphQL schema combining Query and Mutation types
# Strawberry automatically generates the SDL and handles type resolution
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)
