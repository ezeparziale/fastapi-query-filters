from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Planet(Base):
    __tablename__ = "planets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    tags: Mapped[list[str]] = mapped_column(JSON)


class SGTeam(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    members: Mapped[list[str]] = mapped_column(JSON)
    planet_id: Mapped[int | None] = mapped_column(ForeignKey("planets.id"))
    assigned_planet: Mapped[Planet | None] = relationship("Planet")
