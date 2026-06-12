from .database import SessionLocal
from .models import StargateArtifact


def seed_db() -> None:
    db = SessionLocal()
    db.query(StargateArtifact).delete()

    # 1. Active GDO
    gdo = StargateArtifact(
        name="GDO",
        origin_planet="Earth",
        is_destroyed=False,
    )
    # 2. Destroyed Staff Weapon
    weapon = StargateArtifact(
        name="Staff Weapon",
        origin_planet="Chulak",
        is_destroyed=True,
    )
    # 3. Active Zat'nik'tel
    zat = StargateArtifact(
        name="Zat'nik'tel",
        origin_planet="Abydos",
        is_destroyed=False,
    )

    db.add_all([gdo, weapon, zat])
    db.commit()
    db.close()
