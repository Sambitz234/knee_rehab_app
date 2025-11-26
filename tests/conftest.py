import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
import app.database as _app_db

# Import models first so they register with Base, then import the FastAPI app
from app.main import app as fastapi_app


# Use a temporary file-based SQLite database for tests to avoid
# in-memory connection visibility problems across threads.
import tempfile
import os

tmp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
tmp_db_path = tmp_db_file.name
tmp_db_file.close()
TEST_DATABASE_URL = f"sqlite:///{tmp_db_path}"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create all tables once for the test session (models are now imported)
Base.metadata.create_all(bind=engine)

# Patch the application's database SessionLocal/engine to use the test DB so
# tests that import SessionLocal from app.database will use the test DB.
_app_db.SessionLocal = TestingSessionLocal
_app_db.engine = engine


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def client():
    # Override the dependency so FastAPI endpoints use the test DB
    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    # Clean up override
    fastapi_app.dependency_overrides.pop(get_db, None)
    # Remove temporary DB file
    try:
        os.unlink(tmp_db_path)
    except Exception:
        pass
