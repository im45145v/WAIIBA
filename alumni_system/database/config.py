"""
Database configuration and connection settings.
Uses environment variables for sensitive credentials.
"""

import os
from urllib.parse import quote_plus


def get_database_url() -> str:
    """
    Construct database URL from environment variables.
    
    Required environment variables:
        - DB_HOST: Database host (default: localhost)
        - DB_PORT: Database port (default: 5432)
        - DB_NAME: Database name (default: alumni_db)
        - DB_USER: Database username
        - DB_PASSWORD: Database password
    
    Returns:
        PostgreSQL connection URL string.
    """
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ.get("DB_NAME", "alumni_db")
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASSWORD", "")
    
    # URL encode the password to handle special characters
    encoded_password = quote_plus(password)
    
    return f"postgresql://{user}:{encoded_password}@{host}:{port}/{name}"


# SQLAlchemy configuration
SQLALCHEMY_DATABASE_URL = get_database_url()

# Connection pool settings
POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
