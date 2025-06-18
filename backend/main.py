import sys
import os

def setup_database():
    """Run database setup before starting the app"""
    try:
        print("🔄 Setting up database tables...")
        from create_tables import create_tables
        success = create_tables()
        if success:
            print("✅ Database setup completed successfully!")
        else:
            print("❌ Database setup failed!")
            return False
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False
    return True

if __name__ == "__main__":
    # Setup database first
    if not setup_database():
        print("❌ Exiting due to database setup failure")
        sys.exit(1)
    
    # Import and run the FastAPI app
    from app.main import app
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting SoliVolt backend on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
