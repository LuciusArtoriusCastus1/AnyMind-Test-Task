"""
GraphQL Package

This package contains the GraphQL types and resolvers using Strawberry.
Strawberry is a modern Python GraphQL library that leverages type hints for schema definition.

Structure:
- types.py: GraphQL type definitions (inputs and outputs)
- mutations.py: Payment processing mutation
- queries.py: Sales report query

Note: The schema is created in app/main.py with the SQLAlchemy session extension.
"""

from app.graphql.queries import Query
from app.graphql.mutations import Mutation

__all__ = ["Query", "Mutation"]
