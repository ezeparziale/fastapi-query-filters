from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class StargateArtifact(Base):
    __tablename__ = "stargate_artifacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    origin_planet: Mapped[str] = mapped_column(String(50))
    is_destroyed: Mapped[bool] = mapped_column(Boolean, default=False)
    decommissioned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
