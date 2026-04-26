"""
Shared pytest fixtures for backend tests.

Uses an in-memory SQLite database so tests run without a real PostgreSQL server.
The exam table is excluded because it uses a PostgreSQL-specific ARRAY type.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, StaticPool

from app.main import app
from app.db.database import get_session

# Import all models so SQLModel metadata is populated before table creation
import app.models as _models  # noqa: F401

# Tables that are safe to create in SQLite (no PostgreSQL-specific types)
SQLITE_SAFE_TABLES = {
    "tag",
    "question",
    "answer_choice",
    "question_tag",
    "audit_event",
}


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        t for name, t in SQLModel.metadata.tables.items() if name in SQLITE_SAFE_TABLES
    ]
    SQLModel.metadata.create_all(engine, tables=tables)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
