from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create a SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True # Recommended for ensuring connections are live
)

# Create a SessionLocal class to generate database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency to get a database session.
    Ensures the session is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Optional: Function to create all tables in the database (for initial setup or testing)
# You would typically use Alembic for migrations in a production environment.
def init_db():
    # Import Base from your schemas
    # Make sure all your models are imported here or in the module where Base is defined
    # so that Base.metadata knows about them.
    from app.schemas.contract_db_schemas import Base 
    # The following import ensures all models in contract_db_schemas are registered with Base.metadata
    from app.schemas import contract_db_schemas 

    print(f"Creating tables for database at {settings.DATABASE_URL}")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully (if they didn't exist).")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

# Example of how to run init_db if this script is executed directly
# This is useful for initial setup or in development environments.
# In production, you should use Alembic for migrations.
if __name__ == "__main__":
    print("Attempting to initialize the database...")
    # Note: For this to work, your DATABASE_URL in .env or environment variables
    # must point to a running and accessible PostgreSQL instance.
    # Ensure the database specified in DATABASE_URL (e.g., smart_contract_db) exists.
    # The `create_all` command will create tables, not the database itself.
    init_db()
    print("Database initialization process finished.")
