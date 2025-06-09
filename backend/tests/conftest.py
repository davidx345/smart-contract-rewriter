import pytest
from httpx import AsyncClient
from app.main import app # Import your FastAPI app instance
# from app.db.session import get_db, SessionLocal, engine # If testing with a real DB
# from app.db.base import Base # If using SQLAlchemy Base for creating tables

# Example for an in-memory SQLite for testing (if you adapt your session.py for it)
# SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///./test.db"
# engine_test = create_engine(SQLALCHEMY_DATABASE_URL_TEST, connect_args={"check_same_thread": False})
# SessionLocal_test = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# @pytest.fixture(scope="session")
# def db():
#     Base.metadata.create_all(bind=engine_test) # Create tables
#     db = SessionLocal_test()
#     try:
#         yield db
#     finally:
#         db.close()
#         Base.metadata.drop_all(bind=engine_test) # Drop tables after tests

from typing import AsyncGenerator

@pytest.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# If you need to override dependencies for testing (e.g., get_db):
# from app.main import app
# from app.db.session import get_db

# async def override_get_db():
#     try:
#         db = SessionLocal_test() # Use test database
#         yield db
#     finally:
#         db.close()

# app.dependency_overrides[get_db] = override_get_db
