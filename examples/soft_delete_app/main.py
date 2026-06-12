import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_query_filters import FilterDep, FilterValues
from fastapi_query_filters.orm.sqlalchemy import apply_filters

from .database import Base, engine, get_db
from .models import StargateArtifact
from .schemas import StargateArtifactOut
from .seed import seed_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Dropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_db()
    yield


app = FastAPI(title="FastAPI Query Filters Soft-Delete Example", lifespan=lifespan)


@app.get("/artifacts", response_model=list[StargateArtifactOut])
def list_artifacts(
    db: Session = Depends(get_db),
    filters: FilterValues = FilterDep(StargateArtifactOut),
) -> Any:
    """List artifacts with automatic soft-delete filtering (hiding destroyed ones)."""
    stmt = select(StargateArtifact)

    # Apply filters using the library
    stmt = apply_filters(stmt, StargateArtifact, filters)

    # Log the compiled SQL
    logger.info(
        f"Generated SQL: {stmt.compile(engine, compile_kwargs={'literal_binds': True})}"
    )

    artifacts = db.execute(stmt).scalars().all()
    return artifacts
