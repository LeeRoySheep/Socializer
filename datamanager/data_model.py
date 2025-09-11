import datetime
from os import path
from pathlib import Path
from typing import Generator, Optional, List, Dict, Any

from sqlalchemy import (
    Integer,
    String,
    JSON,
    Float,
    Date,
    ForeignKey,
    create_engine,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

# Define Base for SQLAlchemy ORM
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String, default="user")
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)  # JSON for user preferences
    hashed_name: Mapped[str] = mapped_column(String, default="")  # Hashed name for privacy
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    hashed_email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    member_since: Mapped[datetime.date] = mapped_column(Date, default=datetime.date.today)
    messages: Mapped[int] = mapped_column(Integer, default=0)  # Track number of messages sent
    
    # Relationships
    user_skills: Mapped[list["UserSkill"]] = relationship(
        "UserSkill", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    trainings: Mapped[list["Training"]] = relationship("Training", backref="user")
    user_preferences: Mapped[list["UserPreference"]] = relationship("UserPreference", backref="user")

    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, role={self.role})"

    def __str__(self):
        return f"User {self.username} (ID: {self.id})"


class Skill(Base):
    __tablename__ = "skills"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    skill_name: Mapped[str] = mapped_column(String, unique=True, nullable=True)

    # Relationships
    user_skills: Mapped[list["UserSkill"]] = relationship(
        "UserSkill", 
        back_populates="skill", 
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Skill(id={self.id}, skill_name={self.skill_name})"

    def __str__(self) -> str:
        return f"{self.skill_name}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Skill):
            return False
        return self.skill_name == other.skill_name


class UserSkill(Base):
    __tablename__ = "user_skills"
    __table_args__ = (
        UniqueConstraint('user_id', 'skill_id', name='_user_skill_uc'),
        {'sqlite_autoincrement': True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("skills.id", ondelete="CASCADE"), 
        nullable=False
    )
    level: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="user_skills")

    def __repr__(self) -> str:
        return f"UserSkill(user_id={self.user_id}, skill_id={self.skill_id}, level={self.level})"

    def __str__(self) -> str:
        skill_name = self.skill.skill_name if self.skill else "Unknown Skill"
        return f"User {self.user_id} - {skill_name} (Level: {self.level})"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "skill_id": self.skill_id,
            "skill_name": self.skill.skill_name if self.skill else None,
            "level": self.level,
        }


class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False
    )
    preference_type: Mapped[str] = mapped_column(String, nullable=False)  # e.g., 'communication_style', 'interests', 'goals'
    preference_key: Mapped[str] = mapped_column(String, nullable=False)    # Specific preference name
    preference_value: Mapped[dict] = mapped_column(JSON, nullable=False)   # The actual preference value
    confidence: Mapped[float] = mapped_column(Float, default=1.0)          # Confidence score (0-1)
    last_updated: Mapped[datetime.date] = mapped_column(
        Date, 
        default=datetime.date.today, 
        onupdate=datetime.date.today
    )
    
    # Add a composite unique constraint on user_id, preference_type, and preference_key
    __table_args__ = (
        UniqueConstraint('user_id', 'preference_type', 'preference_key'),
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self) -> str:
        return (
            f"UserPreference(id={self.id}, user_id={self.user_id}, "
            f"type={self.preference_type}, key={self.preference_key})"
        )

    def to_dict(self) -> dict:
        """Convert the UserPreference object to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "preference_type": self.preference_type,
            "preference_key": self.preference_key,
            "preference_value": self.preference_value,
            "confidence": self.confidence,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class Training(Base):
    __tablename__ = "training"

    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("skills.id", ondelete="CASCADE"), 
        primary_key=True
    )
    status: Mapped[str] = mapped_column(String, default="pending")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    started_at: Mapped[datetime.date] = mapped_column(
        Date, 
        default=datetime.date.today
    )
    completed_at: Mapped[datetime.date | None] = mapped_column(
        Date, 
        default=None
    )
    notes: Mapped[str | None] = mapped_column(String, default=None)

    def __repr__(self) -> str:
        return (
            f"<Training(user_id={self.user_id}, skill_id={self.skill_id}, "
            f"status={self.status}, progress={self.progress})>"
        )

    def __str__(self) -> str:
        return (
            f"Training for user {self.user_id} on skill {self.skill_id}: "
            f"{self.status} ({self.progress*100:.1f}%)"
        )

    def to_dict(self) -> dict:
        """Convert the Training object to a dictionary."""
        return {
            "user_id": self.user_id,
            "skill_id": self.skill_id,
            "status": self.status,
            "progress": self.progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
        }


class DataModel:
    """
    Database management class for the application.
    Uses SQLAlchemy 2.0 style with type hints and async support.
    """
    def __init__(self, sqlite_file_name: str = "data.sqlite.db") -> None:
        """Initialize the database connection and session factory.
        
        Args:
            sqlite_file_name: Name of the SQLite database file
        """
        self.sqlite_file_name = sqlite_file_name
        self.sqlite_url = f"sqlite:///{self.sqlite_file_name}"
        self.engine = create_engine(
            self.sqlite_url, 
            echo=False, 
            future=True,
            connect_args={"check_same_thread": False}
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine,
            class_=Session,
            expire_on_commit=False
        )

    def create_db_and_tables(self) -> None:
        """Create all database tables defined in the models."""
        Base.metadata.create_all(bind=self.engine)

    def get_db(self) -> Generator[Session, None, None]:
        """
        Get a database session.
        
        Yields:
            Session: A SQLAlchemy database session
            
        Example:
            ```python
            data_model = DataModel()
            with data_model.get_db() as db:
                # Use the database session
                user = db.query(User).first()
            ```
        """
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


if __name__ == "__main__":
    # Example usage:
    data = DataModel()
    print(f"Initializing database at {data.sqlite_url}...")
    if Path(data.sqlite_file_name).exists():
        print("Database already exists, skipping...")
    else:
        data.create_db_and_tables()
        print("Database created.")
