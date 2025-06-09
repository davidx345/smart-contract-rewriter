-- Initialize the database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create additional indexes for better performance
-- These will be created by Alembic migrations, but we can prepare the database

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE smart_contract_rewriter TO postgres;
