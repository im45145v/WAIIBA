-- Alumni Management System - Database Initialization Script
-- =========================================================
-- This script runs automatically when the Docker container starts for the first time.
-- It creates the necessary extensions and sets up the database for the Alumni system.

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- Create indexes for better search performance (after tables are created by SQLAlchemy)
-- Note: These are created here as a reference. The actual tables are created by SQLAlchemy's init_database()

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE alumni_db TO postgres;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Alumni database initialized successfully!';
END $$;
