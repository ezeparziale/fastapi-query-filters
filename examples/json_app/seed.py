import logging

from examples.json_app.database import SessionLocal
from examples.json_app.models import StargateMission

logger = logging.getLogger(__name__)


def seed_db() -> None:
    """Seeds the database with fresh test data."""
    db = SessionLocal()
    try:
        logger.info("Seeding database with fresh data...")
        missions = [
            StargateMission(
                planet_name="Abydos",
                mission_metadata={
                    "commander": "Jack O'Neill",
                    "danger_level": 5,
                    "naquadah_concentration": 0.5,
                    "is_classified": False,
                    "scheduled_date": "1997-07-27",
                    "arrival_time": "20:00:00",
                    "last_report": "1997-07-27T22:00:00",
                },
            ),
            StargateMission(
                planet_name="Chulak",
                mission_metadata={
                    "commander": "Samantha Carter",
                    "danger_level": 7,
                    "naquadah_concentration": 0.2,
                    "is_classified": True,
                    "scheduled_date": "1997-08-01",
                    "arrival_time": "10:30:00",
                    "last_report": "1997-08-01T15:00:00",
                },
            ),
            StargateMission(
                planet_name="Tartarus",
                mission_metadata={
                    "commander": "Teal'c",
                    "danger_level": 10,
                    "naquadah_concentration": 0.9,
                    "is_classified": True,
                    "scheduled_date": "2003-10-10",
                    "arrival_time": "04:00:00",
                    "last_report": "2003-10-11T01:00:00",
                },
            ),
            StargateMission(
                planet_name="P3X-984",
                mission_metadata={
                    "commander": "Janet Fraiser",
                    "danger_level": 3,
                    "naquadah_concentration": 0.05,
                    "is_classified": False,
                    "scheduled_date": "1998-05-12",
                    "arrival_time": "09:00:00",
                    "last_report": "1998-05-12T17:00:00",
                },
            ),
        ]
        db.add_all(missions)
        db.commit()
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()
