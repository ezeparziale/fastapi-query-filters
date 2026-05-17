from typing import Any

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class StargateMission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    planet_name: Mapped[str] = mapped_column(String(255), index=True)
    mission_metadata: Mapped[dict[str, Any]] = mapped_column(JSON)
