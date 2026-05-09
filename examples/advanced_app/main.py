import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from examples.advanced_app.database import Base, engine, get_db
from examples.advanced_app.models import Post
from examples.advanced_app.schemas import PostOut
from examples.advanced_app.seed import seed_db
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


app = FastAPI(title="FastAPI Query Filters Example", lifespan=lifespan)


@app.get("/posts", response_model=list[PostOut])
def list_posts(
    db: Session = Depends(get_db), filters: FilterValues = FilterDep(PostOut)
) -> Any:
    """List posts with automatic filtering, search, and sorting."""
    stmt = select(Post)

    # Apply filters using the library
    stmt = apply_filters(stmt, Post, filters)

    # Log the compiled SQL
    logger.info(
        f"Generated SQL: {stmt.compile(engine, compile_kwargs={'literal_binds': True})}"
    )

    posts = db.execute(stmt).scalars().all()
    return posts
