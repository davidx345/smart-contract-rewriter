#!/usr/bin/env python3
"""
Simple script to create database tables directly using SQLAlchemy.
This creates all tables from both contract and authentication schemas.
"""

import sys
import os

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.schemas.contract_db_schemas import Base
from app.schemas.auth_db_schemas import *  # Import authentication models
from app.models.enterprise_models import *  # Import enterprise models

def create_tables():
    """Create database tables using SQLAlchemy metadata."""
    print(f"Creating tables using database URL: {settings.DATABASE_URL[:50]}...")
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # Create all tables using SQLAlchemy metadata
        Base.metadata.create_all(bind=engine)
        
        print("✅ All tables created successfully using SQLAlchemy metadata!")
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' AND tablename != 'alembic_version'
                ORDER BY tablename
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Database tables: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)
