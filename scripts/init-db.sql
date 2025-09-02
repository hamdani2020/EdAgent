-- Initialize EdAgent database
-- This script sets up the initial database structure

-- Create database if it doesn't exist (for PostgreSQL)
-- Note: This is handled by docker-compose environment variables

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance
-- These will be created by Alembic migrations, but included here for reference

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE edagent TO edagent;