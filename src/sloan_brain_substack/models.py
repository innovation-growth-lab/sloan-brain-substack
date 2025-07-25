"""SQLAlchemy models for storing Substack data."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Newsletter(Base):
    """Model for storing newsletter information."""

    __tablename__ = "newsletters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    author: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    posts: Mapped[list["Post"]] = relationship("Post", back_populates="newsletter")


class Post(Base):
    """Model for storing post information."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(Text)
    published_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)
    post_id: Mapped[Optional[str]] = mapped_column(String(200))  # Substack's internal ID
    content: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Foreign key
    newsletter_id: Mapped[int] = mapped_column(ForeignKey("newsletters.id"))

    # Relationships
    newsletter: Mapped["Newsletter"] = relationship("Newsletter", back_populates="posts")


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, connection_string: str):
        """Initialize database connection.

        Args:
            connection_string: SQLAlchemy connection string (e.g., postgresql://user:pass@host:port/db)
        """
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()

    def close(self):
        """Close the database connection."""
        self.engine.dispose()
