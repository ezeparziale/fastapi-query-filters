import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from tests.models import Base
from tests.seed import seed_db

# Use SQLite in-memory for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def seeded_db(db_session: Session):
    seed_db(db_session)
    return db_session
