import logging
from datetime import UTC, datetime

from examples.basic_app.database import SessionLocal
from examples.basic_app.models import Post, User

logger = logging.getLogger(__name__)


def seed_db() -> None:
    """Seeds the database with fresh test data including deleted posts."""
    db = SessionLocal()
    try:
        logger.info("Seeding database with fresh data...")

        # Create Users
        user1 = User(email="admin@example.com", age=30)
        user2 = User(email="editor@example.com", age=25)
        user3 = User(email="viewer@example.com", age=20)
        db.add_all([user1, user2, user3])
        db.commit()

        # Create Posts (Active and Inactive)
        posts = [
            Post(
                title="FastAPI is awesome",
                description="Content about FastAPI",
                is_active=True,
                author=user1,
            ),
            Post(
                title="SQLAlchemy 2.0 tips",
                description="Deep dive into SA 2.0",
                is_active=True,
                author=user1,
            ),
            Post(
                title="Pydantic V2 migration",
                description="How to migrate to V2",
                is_active=False,
                author=user2,
            ),
            Post(
                title="Python 3.12 features",
                description="What is new in 3.12",
                is_active=True,
                author=user2,
            ),
            Post(
                title="Asyncio patterns",
                description="Learning async in Python",
                is_active=True,
                author=user3,
            ),
        ]

        # Create Deleted Posts
        now = datetime.now(UTC)
        past_date = datetime(2023, 12, 25, tzinfo=UTC)

        deleted_posts = [
            Post(
                title="Deleted Post 1",
                description="This post was recently deleted",
                is_active=False,
                deleted_at=now,
                author=user1,
            ),
            Post(
                title="Old News",
                description="Archive content from long ago",
                is_active=False,
                deleted_at=now,
                author=user2,
            ),
            Post(
                title="Christmas Special (Deleted)",
                description="Special content deleted last year",
                is_active=False,
                deleted_at=past_date,
                author=user1,
            ),
        ]

        db.add_all(posts + deleted_posts)
        db.commit()
        logger.info("Seeding completed successfully (including deleted posts).")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()
