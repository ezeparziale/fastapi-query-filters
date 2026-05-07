from datetime import datetime

from sqlalchemy.orm import Session

from tests.models import Post, User


def seed_db(db: Session) -> None:
    # Clear existing data
    db.query(Post).delete()
    db.query(User).delete()

    # Create Users (Stargate SG-1 Characters)
    user1 = User(
        email="oneill@example.com",
        name="Jack O'Neill",
        age=50,
        is_active=True,
        created_at=datetime(2026, 1, 1),
        health_status=95.5,
    )
    user2 = User(
        email="carter@example.com",
        name="Samantha Carter",
        age=35,
        is_active=True,
        created_at=datetime(2026, 2, 1),
        health_status=100.0,
    )
    user3 = User(
        email="tealc@example.com",
        name="Teal'c",
        age=157,
        is_active=False,
        created_at=datetime(2026, 3, 1),
        health_status=100.0,
    )

    db.add_all([user1, user2, user3])
    db.commit()

    # Create Posts (Stargate SG-1 Episodes/Themes)
    post1 = Post(
        title="Children of the Gods",
        content="The first mission to Chulak to rescue Sha're and Skaara.",
        author=user1,
        created_at=datetime(2026, 4, 1),
    )
    post2 = Post(
        title="Window of Opportunity",
        content="In the middle of my backswing! A time loop episode.",
        author=user1,
        created_at=datetime(2026, 5, 1),
    )
    post3 = Post(
        title="The Fifth Race",
        content="Jack receives the knowledge of the Ancients in his brain.",
        author=user2,
        created_at=datetime(2026, 6, 1),
    )

    db.add_all([post1, post2, post3])
    db.commit()
