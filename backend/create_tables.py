#!/usr/bin/env python3
"""
Simple script to create database tables directly using SQLAlchemy.
This bypasses Alembic entirely and just creates what we need.
"""

import sys
import os

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.schemas.contract_db_schemas import Base

def create_tables():
    """Create database tables only if they don't exist."""
    print(f"Checking/creating tables using database URL: {settings.DATABASE_URL[:50]}...")
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # Check which tables already exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' AND tablename != 'alembic_version'
            """))
            existing_tables = [row[0] for row in result.fetchall()]
            print(f"🔍 Existing tables in database: {', '.join(sorted(existing_tables))}")
            
            required_tables = ['users', 'contract_analyses', 'contract_rewrites', 'contract_generations', 'gemini_api_logs']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if not missing_tables:
                print("✅ All required tables already exist. Skipping creation.")
                print(f"📋 Contract tables: {', '.join([t for t in existing_tables if t in required_tables])}")
                return True
            else:
                print(f"🔨 Missing tables: {', '.join(missing_tables)}")
                print("Creating missing tables...")
        
        # Use raw SQL to create tables in correct order with better error handling
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            try:
                # Create users table first (if missing)
                if 'users' in missing_tables:
                    print("  Creating table: users")
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR UNIQUE,
                            email VARCHAR UNIQUE,
                            hashed_password VARCHAR,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                        )
                    """))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_id ON users (id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_username ON users (username)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
                    print("  ✅ Created: users")
                
                # Create contract_analyses table (if missing)
                if 'contract_analyses' in missing_tables:
                    print("  Creating table: contract_analyses")
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS contract_analyses (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER,  -- Removed REFERENCES users(id)
                            contract_name VARCHAR(255),
                            original_code TEXT NOT NULL,
                            analysis_report JSON NOT NULL,
                            vulnerabilities_found JSON,
                            gas_analysis JSON,
                            requested_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                            completed_at TIMESTAMP WITH TIME ZONE
                        )
                    """))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_contract_analyses_id ON contract_analyses (id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_contract_analyses_user_id ON contract_analyses (user_id)")) # Add index for user_id
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_contract_analyses_contract_name ON contract_analyses (contract_name)"))
                    print("  ✅ Created: contract_analyses")
                
                # Create contract_rewrites table (if missing)
                if 'contract_rewrites' in missing_tables:
                    print("  Creating table: contract_rewrites")
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS contract_rewrites (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER,  -- Removed REFERENCES users(id)
                            analysis_id INTEGER REFERENCES contract_analyses(id),
                            contract_name VARCHAR(255),
                            original_code TEXT NOT NULL,
                            rewritten_code TEXT NOT NULL,
                            optimization_goals VARCHAR[],
                            rewrite_summary JSON,
                            requested_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                            completed_at TIMESTAMP WITH TIME ZONE
                        )
                    """))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_contract_rewrites_id ON contract_rewrites (id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_contract_rewrites_user_id ON contract_rewrites (user_id)")) # Add index for user_id                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_contract_rewrites_contract_name ON contract_rewrites (contract_name)"))
                    print("  ✅ Created: contract_rewrites")
                
                # Create contract_generations table (if missing)
                if 'contract_generations' in missing_tables:
                    print("  Creating table: contract_generations")
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS contract_generations (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER,  -- Removed REFERENCES users(id)
                            contract_name VARCHAR(255),
                            description TEXT NOT NULL,
                            features VARCHAR[],
                            generated_code TEXT NOT NULL,
                            generation_metadata JSON,
                            compiler_version VARCHAR(50),
                            requested_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                            completed_at TIMESTAMP WITH TIME ZONE
                        )
                    """))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_contract_generations_id ON contract_generations (id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_contract_generations_user_id ON contract_generations (user_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_contract_generations_contract_name ON contract_generations (contract_name)"))
                    print("  ✅ Created: contract_generations")
                
                # Create gemini_api_logs table (if missing)
                if 'gemini_api_logs' in missing_tables:
                    print("  Creating table: gemini_api_logs")
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS gemini_api_logs (
                            id SERIAL PRIMARY KEY,
                            request_payload JSON NOT NULL,
                            response_payload JSON,
                            error_message TEXT,
                            called_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                            duration_ms INTEGER,
                            related_analysis_id INTEGER REFERENCES contract_analyses(id),
                            related_rewrite_id INTEGER REFERENCES contract_rewrites(id)
                        )
                    """))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_gemini_api_logs_id ON gemini_api_logs (id)"))
                    print("  ✅ Created: gemini_api_logs")
                
                # Commit the transaction
                trans.commit()
                print("✅ All tables created successfully!")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error in transaction: {e}")
                return False
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' AND tablename != 'alembic_version'
                ORDER BY tablename
            """))
            tables = [row[0] for row in result.fetchall()]
            contract_tables = [t for t in tables if t in ['users', 'contract_analyses', 'contract_rewrites', 'contract_generations', 'gemini_api_logs']]
            print(f"📋 Contract tables available: {', '.join(contract_tables)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)
