"""
Application Configuration

This module handles all configuration settings for the application using pydantic-settings.
Configuration can be loaded from environment variables or a .env file.

Key Settings:
- DATABASE_URL: PostgreSQL connection string for async operations
- DEBUG: Enable debug mode for development
- APP_NAME: Application name used in logging and documentation
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        APP_NAME: Name of the application
        DEBUG: Debug mode flag
        DATABASE_URL: PostgreSQL connection URL (async format using asyncpg)
        TEST_DATABASE_URL: Database URL for testing (uses SQLite for simplicity)
    """

    APP_NAME: str = "AnyMind POS Payment System"
    DEBUG: bool = False

    # Database configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/anymind_pos"

    # Test database (PostgreSQL for full compatibility)
    TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/anymind_pos_test"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses LRU cache to ensure settings are only loaded once from environment.
    This improves performance and ensures consistency across the application.

    Returns:
        Settings: Application settings instance
    """
    return Settings()
