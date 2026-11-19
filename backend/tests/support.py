"""Shared test harness. Runs on SQLite by default; set TEST_DATABASE_URL to a PostgreSQL URL
(postgresql+psycopg://user:pass@host/db) to run the same suite on the production engine (CI does)."""

import os

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite://")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-tests-123456"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.entities import Drama

IS_SQLITE = TEST_DATABASE_URL.startswith("sqlite")
if IS_SQLITE:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(TEST_DATABASE_URL)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def reset_database() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestingSession() as db:
        db.add(
            Drama(
                id=1,
                title="Drama test",
                synopsis="Une histoire",
                poster_url="https://example.com/p.jpg",
                banner_url="https://example.com/b.jpg",
                country="Bénin",
                categories=["Romance"],
                rating=9.1,
                is_published=True,
            )
        )
        db.commit()
        if not IS_SQLITE:  # explicit ids do not advance the PostgreSQL sequence
            db.execute(text("SELECT setval(pg_get_serial_sequence('dramas','id'), 1000)"))
            db.commit()


def register_user(email="journey@example.com", password="StrongPass!123"):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": password},
    )
    assert r.status_code == 201, r.text
    return r.json()
