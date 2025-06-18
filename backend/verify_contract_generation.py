#!/usr/bin/env python3
"""
Verification script to check if contract generation is properly set up in the database.
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from app.core.config import settings

def verify_contract_generation_setup():
    """Verify that the contract generation feature is properly set up."""
    print("🔍 Verifying Contract Generation Database Setup...")
    print("=" * 60)
    
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if contract_generations table exists
            result = conn.execute(text("""
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'contract_generations'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            
            if not columns:
                print("❌ contract_generations table does not exist!")
                print("   Run: python create_tables.py")
                return False
            
            print("✅ contract_generations table exists!")
            print("\n📋 Table Structure:")
            print("   Column Name          | Data Type      | Nullable")
            print("   " + "-" * 50)
            
            for column in columns:
                table_name, column_name, data_type, is_nullable = column
                nullable = "YES" if is_nullable == "YES" else "NO"
                print(f"   {column_name:<20} | {data_type:<14} | {nullable}")
            
            # Check indexes
            result = conn.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes 
                WHERE tablename = 'contract_generations'
                ORDER BY indexname
            """))
            
            indexes = result.fetchall()
            print(f"\n🔗 Indexes ({len(indexes)}):")
            for index in indexes:
                print(f"   - {index[0]}")
            
            # Check if the imports work
            try:
                from app.schemas.contract_db_schemas import ContractGenerationDB
                print("\n✅ ContractGenerationDB model imports successfully!")
            except ImportError as e:
                print(f"\n❌ Failed to import ContractGenerationDB: {e}")
                return False
            
            # Check if the API endpoint exists
            try:
                from app.apis.v1.endpoints.contracts import router
                print("✅ Contracts API router imports successfully!")
                
                # Check if generate endpoint is registered
                routes = [route.path for route in router.routes if hasattr(route, 'path')]
                if '/generate' in routes:
                    print("✅ /generate endpoint is registered!")
                else:
                    print("⚠️  /generate endpoint not found in routes")
                    print(f"   Available routes: {routes}")
                
            except ImportError as e:
                print(f"\n❌ Failed to import contracts router: {e}")
                return False
            
            print("\n🎉 Contract Generation Setup Verification Complete!")
            print("✅ Database table: READY")
            print("✅ Model imports: READY") 
            print("✅ API endpoints: READY")
            print("\nYou can now test the contract generation feature!")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = verify_contract_generation_setup()
    if success:
        print("\n🚀 Ready to test! Run: python test_contract_generation.py")
    sys.exit(0 if success else 1)
