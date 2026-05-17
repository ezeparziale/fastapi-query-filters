import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy.orm import Session

from tests.models import Mission, Post, Team, User


def seed_db(db: Session) -> None:
    """Seeds the database with fresh SG-1 test data."""
    # Clear existing data
    db.query(Mission).delete()
    db.query(Post).delete()
    db.query(User).delete()
    db.query(Team).delete()
    db.commit()

    # Create Teams
    team_sg1 = Team(name="SG-1", description="Flagship Stargate exploration team")
    team_sg3 = Team(name="SG-3", description="Marine combat unit")
    team_medical = Team(name="Medical", description="SGC Medical staff")
    db.add_all([team_sg1, team_sg3, team_medical])
    db.commit()

    # Create Users
    user1 = User(
        name="Jack O'Neill",
        email="j.oneill@sgc.mil",
        age=45,
        profile_bio="That's O'Neill, with two L's.",
        team=team_sg1,
        rank="Colonel",
        is_alien=False,
        clearance_level=9,
        health_status=95.5,
        date_of_birth=date(1952, 10, 20),
        last_login_ip="192.168.1.10",
        uuid_badge=uuid.UUID("7452f110-31f7-4363-8877-2485966624d7"),
    )
    user2 = User(
        name="Samantha Carter",
        email="s.carter@sgc.mil",
        age=35,
        profile_bio="Astrophysicist and MacGyver of the team.",
        team=team_sg1,
        rank="Major",
        is_alien=False,
        clearance_level=8,
        health_status=100.0,
        date_of_birth=date(1968, 12, 29),
        last_login_ip="192.168.1.11",
        uuid_badge=uuid.UUID("16fd2706-8baf-433b-82eb-8c7fada847da"),
    )
    user3 = User(
        name="Teal'c",
        email="tealc@sgc.mil",
        age=105,
        profile_bio="Indeed.",
        team=team_sg1,
        rank="Civilian",
        is_alien=True,
        clearance_level=7,
        health_status=100.0,
        date_of_birth=date(1899, 1, 1),
        last_login_ip="192.168.1.12",
        uuid_badge=uuid.UUID("d05c08f4-2c67-4e78-9538-42845a703714"),
    )
    user4 = User(
        name="Janet Fraiser",
        email="j.fraiser@sgc.mil",
        age=38,
        profile_bio="Chief Medical Officer.",
        team=team_medical,
        rank="Doctor",
        is_alien=False,
        clearance_level=7,
        health_status=100.0,
        date_of_birth=date(1965, 5, 5),
        last_login_ip="192.168.1.50",
        uuid_badge=uuid.UUID("52843063-42e7-4934-802c-7b70744747c3"),
    )

    db.add_all([user1, user2, user3, user4])
    db.commit()

    # Create Posts (Mission Reports)
    posts = [
        Post(
            title="Mission to Abydos",
            description="Initial reconnaissance mission. Encountered Ra.",
            is_active=True,
            gate_address="P8X-412",
            casualties=0,
            success_rate=99.9,
            mission_report_url="http://sgc.mil/reports/abydos",
            mission_date=date(1997, 7, 27),
            mission_start=datetime(1997, 7, 27, 20, 0, tzinfo=UTC),
            incident_time=time(20, 15),
            created_at=datetime(1997, 7, 28, 9, 0, tzinfo=UTC),
            updated_at=datetime(1997, 7, 28, 9, 0, tzinfo=UTC),
            author=user1,
        ),
        Post(
            title="Encounter in Chulak",
            description="Rescued prisoners, gained new team member.",
            is_active=True,
            gate_address="P3X-123",
            casualties=1,
            success_rate=85.5,
            mission_report_url="http://sgc.mil/reports/chulak",
            mission_date=date(1997, 8, 1),
            mission_start=datetime(1997, 8, 1, 10, 30, tzinfo=UTC),
            incident_time=time(11, 45),
            created_at=datetime(1997, 8, 2, 14, 0, tzinfo=UTC),
            updated_at=datetime(1997, 8, 2, 14, 0, tzinfo=UTC),
            author=user2,
        ),
        Post(
            title="Medical supplies inventory",
            description="Monthly audit of infirmary supplies.",
            is_active=True,
            gate_address=None,
            casualties=None,
            success_rate=None,
            mission_report_url=None,
            mission_date=date(1997, 8, 15),
            mission_start=datetime(1997, 8, 15, 9, 0, tzinfo=UTC),
            incident_time=time(10, 0),
            created_at=datetime(1997, 8, 15, 17, 0, tzinfo=UTC),
            updated_at=datetime(1997, 8, 15, 17, 0, tzinfo=UTC),
            author=user4,
        ),
    ]

    # Create Deleted Posts
    deleted_posts = [
        Post(
            title="Contact with Asgard (Classified/Deleted)",
            description="First contact. Record expunged.",
            is_active=False,
            gate_address="OTH-ALA",
            casualties=0,
            success_rate=100.0,
            mission_report_url="http://sgc.mil/reports/classified-1",
            mission_date=date(1997, 9, 26),
            mission_start=datetime(1997, 9, 26, 23, 0, tzinfo=UTC),
            incident_time=time(23, 30),
            created_at=datetime(1997, 9, 27, 8, 0, tzinfo=UTC),
            updated_at=datetime(1997, 9, 27, 8, 0, tzinfo=UTC),
            deleted_at=datetime(1998, 1, 1, 12, 0, tzinfo=UTC),
            author=user1,
        ),
    ]

    db.add_all(posts + deleted_posts)
    db.commit()

    # Create Missions with JSON metadata
    missions = [
        Mission(
            planet_name="P3X-984",
            mission_metadata={
                "commander": "Jack O'Neill",
                "danger_level": 8,
                "naquadah_concentration": 0.85,
                "is_classified": True,
                "scheduled_date": "1997-10-15",
                "arrival_time": "08:30:00",
                "last_report": "1997-10-15T12:00:00",
            },
        ),
        Mission(
            planet_name="P4X-639",
            mission_metadata={
                "commander": "Samantha Carter",
                "danger_level": 4,
                "naquadah_concentration": 0.15,
                "is_classified": False,
                "scheduled_date": "1998-03-22",
                "arrival_time": "14:15:00",
                "last_report": "1998-03-22T18:45:00",
            },
        ),
        Mission(
            planet_name="P2X-555",
            mission_metadata={
                "commander": "Teal'c",
                "danger_level": 10,
                "naquadah_concentration": 0.95,
                "is_classified": True,
                "scheduled_date": "1999-01-01",
                "arrival_time": "00:00:00",
                "last_report": "1999-01-01T06:00:00",
            },
        ),
        Mission(planet_name="Empty Planet", mission_metadata=None),
        Mission(
            planet_name="Partial Data Planet",
            mission_metadata={"commander": "Daniel Jackson"},
        ),
    ]
    db.add_all(missions)
    db.commit()
