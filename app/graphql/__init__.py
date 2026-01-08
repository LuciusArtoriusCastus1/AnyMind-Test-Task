"""
GraphQL Package

This package contains the GraphQL schema, types, and resolvers using Strawberry.
Strawberry is a modern Python GraphQL library that leverages type hints for schema definition.

Structure:
- types.py: GraphQL type definitions (inputs and outputs)
- mutations.py: Payment processing mutation
- queries.py: Sales report query
- schema.py: Main schema combining queries and mutations
"""

from app.graphql.schema import schema

__all__ = ["schema"]
