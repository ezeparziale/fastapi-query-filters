import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Time,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    members: Mapped[list["User"]] = relationship(back_populates="team")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), default="Unknown")
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    age: Mapped[int] = mapped_column()
    profile_bio: Mapped[str | None] = mapped_column(String(500), nullable=True)

    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    rank: Mapped[str] = mapped_column(String(50), default="Civilian")
    is_alien: Mapped[bool] = mapped_column(Boolean, default=False)
    clearance_level: Mapped[int] = mapped_column(Integer, default=1)
    health_status: Mapped[float] = mapped_column(Float, default=100.0)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    uuid_badge: Mapped[uuid.UUID] = mapped_column(Uuid, default=uuid.uuid4)

    team: Mapped["Team | None"] = relationship(back_populates="members")
    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    gate_address: Mapped[str | None] = mapped_column(String(7), nullable=True)
    casualties: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    mission_report_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    mission_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    mission_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    incident_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    author: Mapped["User"] = relationship(back_populates="posts")
