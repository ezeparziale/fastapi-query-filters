from collections.abc import Generator

import pytest
from pydantic import BaseModel, Field
from sqlalchemy import Engine, ForeignKey, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from fastapi_query_filters import FilterValues
from fastapi_query_filters.core import create_filter_model
from fastapi_query_filters.orm.sqlalchemy import apply_filters


# --- Local Models for Testing Nested Joins ---
class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = "test_teams"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    members: Mapped[list["User"]] = relationship(back_populates="team")


class User(Base):
    __tablename__ = "test_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    team_id: Mapped[int] = mapped_column(ForeignKey("test_teams.id"))
    team: Mapped["Team"] = relationship(back_populates="members")
    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "test_posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50))
    user_id: Mapped[int] = mapped_column(ForeignKey("test_users.id"))
    author: Mapped["User"] = relationship(back_populates="posts")


# --- Pydantic Schemas ---
class TeamOut(BaseModel):
    name: str = Field(json_schema_extra={"filters": ["eq"]})


class UserOut(BaseModel):
    name: str = Field(json_schema_extra={"filters": ["eq"]})
    team: TeamOut


class PostOut(BaseModel):
    title: str = Field(json_schema_extra={"filters": ["eq"]})
    author: UserOut

    class FilterConfig:
        max_depth = 2
        prefix = "f_"


@pytest.fixture
def nested_db(engine: Engine) -> Generator[Session, None, None]:
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        t1 = Team(name="Red")
        t2 = Team(name="Blue")
        session.add_all([t1, t2])
        session.commit()

        u1 = User(name="Alice", team=t1)
        u2 = User(name="Bob", team=t2)
        session.add_all([u1, u2])
        session.commit()

        p1 = Post(title="Post 1", author=u1)
        p2 = Post(title="Post 2", author=u2)
        session.add_all([p1, p2])
        session.commit()

        yield session
    Base.metadata.drop_all(engine)


def test_nested_join_filtering(nested_db: Session) -> None:
    """Verify that filtering by author__team__name works with max_depth=2."""
    FilterModel = create_filter_model(PostOut)

    # Should have f_author__team__name__eq
    assert "f_author__team__name__eq" in FilterModel.model_fields

    filters = FilterValues(FilterModel(f_author__team__name__eq="Red"))

    stmt = select(Post)
    stmt = apply_filters(stmt, Post, filters)

    results = nested_db.execute(stmt).scalars().all()
    assert len(results) == 1
    assert results[0].title == "Post 1"
    assert results[0].author.team.name == "Red"


def test_nested_join_depth_exceeded() -> None:
    """Verify that fields beyond max_depth are not generated."""

    class ShallowPostOut(PostOut):
        class FilterConfig:
            max_depth = 1
            prefix = "f_"

    FilterModel = create_filter_model(ShallowPostOut)

    # Should have f_author__name__eq (depth 1)
    assert "f_author__name__eq" in FilterModel.model_fields
    # Should NOT have f_author__team__name__eq (depth 2)
    assert "f_author__team__name__eq" not in FilterModel.model_fields
