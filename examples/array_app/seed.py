import logging

from examples.array_app.database import SessionLocal
from examples.array_app.models import Planet, SGTeam

logger = logging.getLogger(__name__)


def seed_db() -> None:
    db = SessionLocal()
    try:
        logger.info("Seeding Stargate data...")
        abydos = Planet(name="Abydos", tags=["desert", "ancient", "friendly"])
        chulak = Planet(name="Chulak", tags=["jaffa", "forest", "hostile"])
        p3x_984 = Planet(name="P3X-984", tags=["alpha_site", "mountains"])

        db.add_all([abydos, chulak, p3x_984])
        db.flush()

        sg1 = SGTeam(
            name="SG-1",
            members=["Jack O'Neill", "Samantha Carter", "Daniel Jackson", "Teal'c"],
            assigned_planet=chulak,
        )
        sg2 = SGTeam(
            name="SG-2",
            members=["Charles Kawalsky", "Warren", "Casey"],
            assigned_planet=abydos,
        )

        db.add_all([sg1, sg2])
        db.commit()
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()
