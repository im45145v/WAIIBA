"""
Database initialization and migration utilities.
"""

from typing import Optional

from sqlalchemy import text

from .connection import engine
from .models import Base


def init_database() -> None:
    """
    Initialize the database by creating all tables.
    
    This function should be called on application startup
    or during deployment to ensure all tables exist.
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables() -> None:
    """
    Drop all tables from the database.
    
    WARNING: This will delete all data. Use with caution.
    """
    Base.metadata.drop_all(bind=engine)


def reset_database() -> None:
    """
    Reset the database by dropping and recreating all tables.
    
    WARNING: This will delete all data. Use with caution.
    """
    drop_all_tables()
    init_database()


def check_database_connection() -> bool:
    """
    Check if the database connection is working.
    
    Returns:
        True if connection is successful, False otherwise.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def get_table_counts() -> dict[str, int]:
    """
    Get the row count for each table in the database.
    
    Returns:
        Dictionary mapping table names to row counts.
    """
    counts = {}
    with engine.connect() as connection:
        for table in Base.metadata.tables:
            result = connection.execute(
                text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
            )
            counts[table] = result.scalar() or 0
    return counts
