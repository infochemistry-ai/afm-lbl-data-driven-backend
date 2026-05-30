import pytest
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer

from app.db.base import Base
from app.db import models  # noqa: F401  (populate metadata)
from app.services.polyelectrolytes import seed_catalog


@pytest.fixture(scope="session")
def pg_url():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg.get_connection_url().replace("psycopg2", "psycopg")


@pytest.fixture
def db_session(pg_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", pg_url)
    from app.config import get_settings
    get_settings.cache_clear()
    from app.db.session import get_engine, get_session_factory
    import app.db.session as s
    s._engine = None
    s._session_factory = None
    engine = get_engine()
    Base.metadata.create_all(engine)
    factory = get_session_factory()
    session: Session = factory()
    seed_catalog(session)
    yield session
    session.close()
    Base.metadata.drop_all(engine)
