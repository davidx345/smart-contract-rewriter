
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
import os

Base = declarative_base()

class ContractAnalysis(Base):
    __tablename__ = "contract_analysis"
    id = Column(Integer, primary_key=True, index=True)
    contract_name = Column(String, nullable=False)
    source_code = Column(Text, nullable=False)
    analysis_result = Column(Text)
    requested_at = Column(DateTime)

# Add more models here as needed

def create_tables():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set in environment.")
        return False

    print(f"Creating tables using database URL: {db_url[:50]}...")

    engine = create_engine(db_url)
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(
                """
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' AND tablename != 'alembic_version'
                ORDER BY tablename
                """
            )
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
    exit(0 if success else 1)
