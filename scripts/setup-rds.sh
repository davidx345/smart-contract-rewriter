#!/bin/bash
# RDS Connection Script for EC2

echo "🔐 Smart Contract RDS Setup Script"
echo "==================================="
echo ""

# RDS Connection Details
RDS_ENDPOINT="smart-contract-db.c050cs4y6jjo.us-east-1.rds.amazonaws.com"
RDS_PORT="5432"
RDS_USER="postgres"
RDS_PASSWORD="SecurePassword123"
RDS_DATABASE="smart_contract_db"

echo "📋 Connection Details:"
echo "  Endpoint: $RDS_ENDPOINT"
echo "  Port: $RDS_PORT"
echo "  Database: $RDS_DATABASE"
echo "  User: $RDS_USER"
echo ""

# Test connection
echo "🔍 Testing RDS connection..."
export PGPASSWORD="$RDS_PASSWORD"

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    echo "📦 Installing PostgreSQL client..."
    sudo yum update -y
    sudo yum install -y postgresql15
fi

# Test connection
echo "🔗 Connecting to RDS..."
psql -h "$RDS_ENDPOINT" -p "$RDS_PORT" -U "$RDS_USER" -d "$RDS_DATABASE" -c "SELECT version();"

if [ $? -eq 0 ]; then
    echo "✅ Connection successful!"
    echo ""
    echo "🏗️ Creating Smart Contract database schema..."
    
    # Create the database schema
    psql -h "$RDS_ENDPOINT" -p "$RDS_PORT" -U "$RDS_USER" -d "$RDS_DATABASE" << 'EOF'
-- Smart Contract Database Schema
CREATE SCHEMA IF NOT EXISTS smart_contract;

-- Users table
CREATE TABLE IF NOT EXISTS smart_contract.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contracts table
CREATE TABLE IF NOT EXISTS smart_contract.contracts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES smart_contract.users(id),
    original_code TEXT NOT NULL,
    analyzed_code TEXT,
    rewritten_code TEXT,
    analysis_result JSONB,
    rewrite_result JSONB,
    contract_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON smart_contract.users(email);
CREATE INDEX IF NOT EXISTS idx_contracts_user_id ON smart_contract.contracts(user_id);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON smart_contract.contracts(status);

-- Display created tables
\dt smart_contract.*

EOF
    
    echo "✅ Database schema created successfully!"
else
    echo "❌ Connection failed!"
    echo "Check security groups and network configuration."
fi
