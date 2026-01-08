"""
FastAPI Application Entry Point

This is the main application module that:
1. Creates and configures the FastAPI application
2. Sets up the GraphQL endpoint using Strawberry
3. Manages database connections and lifecycle events

Application Features:
- GraphQL endpoint at /graphql with GraphiQL playground
- Health check endpoint at /health
- Async database operations with PostgreSQL
- Connection pooling for handling concurrent requests
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from strawberry.extensions import SchemaExtension
import strawberry

from app.config import get_settings
from app.database import init_db, close_db, AsyncSessionLocal
from app.graphql.queries import Query
from app.graphql.mutations import Mutation

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - On startup: Initialize database tables
    - On shutdown: Close database connections

    Using the modern lifespan context manager pattern instead of
    deprecated on_event decorators.
    """
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Close database connections
    await close_db()


class SQLAlchemySessionExtension(SchemaExtension):
    """
    Strawberry extension for managing SQLAlchemy async session lifecycle.

    This extension ensures that:
    1. A database session is created for each request
    2. The session is committed on success
    3. The session is rolled back on error
    4. The session is properly closed after the request
    """

    async def on_request_start(self):
        session = AsyncSessionLocal()
        self.execution_context.context["db"] = session

    async def on_request_end(self):
        db = self.execution_context.context.get("db")
        if db:
            try:
                await db.commit()
            except Exception:
                await db.rollback()
                raise
            finally:
                await db.close()


async def get_context(request: Request) -> dict:
    """
    Create GraphQL context for each request.

    The context is passed to all resolvers and contains:
    - request: The FastAPI request object
    - db: Will be populated by SQLAlchemySessionExtension

    This enables dependency injection pattern in GraphQL resolvers.
    """
    return {"request": request}


# Create the GraphQL schema with session management extension
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[SQLAlchemySessionExtension],
)

# Create GraphQL router with Strawberry
# graphiql=True enables the interactive GraphQL playground
graphql_router = GraphQLRouter(
    schema=schema,
    context_getter=get_context,
    graphiql=True,  # Enable GraphiQL playground at /graphql
)

# Create the FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    POS E-commerce Payment System API

    A GraphQL API for processing payments with multiple payment methods,
    calculating final prices based on price modifiers, and awarding
    loyalty points.

    ## Features

    - **Payment Processing**: Accept payments with various methods
    - **Dynamic Pricing**: Apply price modifiers within allowed ranges
    - **Loyalty Points**: Award points based on payment method
    - **Sales Reporting**: Query hourly sales data by date range

    ## GraphQL Endpoint

    - **Playground**: Visit /graphql for the interactive GraphQL playground
    - **Endpoint**: POST /graphql for queries and mutations
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware for cross-origin requests
# In production, restrict origins to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the GraphQL router
app.include_router(graphql_router, prefix="/graphql")


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Used by load balancers and orchestration systems to verify
    the application is running and responsive.

    Returns:
        dict: Status and application information
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.

    Provides basic information about the API and links to
    the GraphQL playground.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "graphql_endpoint": "/graphql",
        "health_endpoint": "/health",
        "documentation": "/docs",
    }
