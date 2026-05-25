import os
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from tests.models import Base
from tests.seed import seed_db

# Defaults to SQLite in-memory, but can be overridden to run the same suite
# against MySQL/PostgreSQL, e.g. TEST_DATABASE_URL=postgresql+psycopg://...
SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    connect_args = {}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine: Engine) -> Generator[Session, None, None]:
    # Full schema reset per test keeps data and autoincrement/identity deterministic
    # across SQLite, PostgreSQL and MySQL.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    connection = engine.connect()
    outer_transaction = connection.begin()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = session_factory()
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess: Session, trans: Any) -> None:
        # Reopen SAVEPOINT after each commit/rollback inside a test,
        # keeping per-test isolation stable across dialects.
        if trans.nested and not sess.in_nested_transaction():
            sess.begin_nested()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def seeded_db(db_session: Session) -> Session:
    seed_db(db_session)
    return db_session
