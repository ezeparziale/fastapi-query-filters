import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from examples.array_app.database import Base, engine, get_db
from examples.array_app.models import SGTeam
from examples.array_app.schemas import TeamOut
from examples.array_app.seed import seed_db
from fastapi_query_filters import FilterDep, FilterValues
from fastapi_query_filters.orm.sqlalchemy import apply_filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_db()
    yield


app = FastAPI(title="Stargate Array Filter API", lifespan=lifespan)


@app.get("/teams", response_model=list[TeamOut])
def get_teams(
    db: Session = Depends(get_db), filters: FilterValues = FilterDep(TeamOut)
) -> Any:
    stmt = select(SGTeam)
    stmt = apply_filters(stmt, SGTeam, filters)

    results = db.execute(stmt).scalars().all()
    return results
