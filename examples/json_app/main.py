import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from examples.json_app.database import Base, engine, get_db
from examples.json_app.models import StargateMission
from examples.json_app.schemas import MissionOut
from examples.json_app.seed import seed_db
from fastapi_query_filters import FilterDep, FilterValues
from fastapi_query_filters.orm.sqlalchemy import apply_filters

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


app = FastAPI(title="Stargate JSON Filter API", lifespan=lifespan)


@app.get("/missions", response_model=list[MissionOut])
def get_missions(
    db: Session = Depends(get_db), filters: FilterValues = FilterDep(MissionOut)
) -> Any:
    # Build the base SQLAlchemy statement
    stmt = select(StargateMission)

    # Apply dynamic filters, including JSON path extraction and casting
    stmt = apply_filters(stmt, StargateMission, filters)

    # Log the compiled SQL
    logger.info(
        f"Generated SQL: {stmt.compile(engine, compile_kwargs={'literal_binds': True})}"
    )

    results = db.execute(stmt).scalars().all()
    return results
