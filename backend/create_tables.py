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
            
            required_tables = ['users', 'contract_analyses', 'contract_rewrites', 'gemini_api_logs']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if not missing_tables:
                print("✅ All required tables already exist. Skipping creation.")
                print(f"📋 Existing tables: {', '.join(sorted(existing_tables))}")
                return True
            else:
                print(f"🔨 Missing tables: {', '.join(missing_tables)}")
                print("Creating missing tables...")
        
        # Import the individual table classes
        from app.schemas.contract_db_schemas import User, ContractAnalysisDB, ContractRewriteDB, GeminiAPILogDB
        
        # Create tables in dependency order (parent tables first)
        table_creation_order = [
            ("users", User.__table__),
            ("contract_analyses", ContractAnalysisDB.__table__), 
            ("contract_rewrites", ContractRewriteDB.__table__),
            ("gemini_api_logs", GeminiAPILogDB.__table__)
        ]
        
        for table_name, table_obj in table_creation_order:
            if table_name in missing_tables:
                try:
                    print(f"  Creating table: {table_name}")
                    table_obj.create(bind=engine, checkfirst=True)
                    print(f"  ✅ Created: {table_name}")
                except Exception as e:
                    print(f"  ❌ Error creating {table_name}: {e}")
                    # Continue with other tables even if one fails
        
        print("✅ Table creation process completed!")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' AND tablename != 'alembic_version'
                ORDER BY tablename
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Final tables: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)
