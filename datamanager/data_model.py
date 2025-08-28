import datetime
from os import path
from typing import Generator

from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
    Float,
    Date,
    ForeignKey,
    create_engine,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define Base for SQLAlchemy ORM
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    role = Column(String, default="user")
    temperature = Column(Float, default=0.7)
    preferences = Column(JSON, default="{}")  # JSON string for user preferences
    hashed_name = Column(String, default=None)
    hashed_password = Column(String, default=None)
    hashed_email = Column(String, default=None)
    member_since = Column(Date, default=datetime.datetime.now().date())
    messages = Column(JSON, default="[]")  # JSON string for user messages

    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, role={self.role})"

    def __str__(self):
        return f"User {self.username} (ID: {self.id})"


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String, default=None, unique=True)

    def __repr__(self):
        return f"Skill(id={self.id}, name={self.skill_name})"

    def __str__(self):
        return f"Skill {self.skill_name} (Level: {self.level})"

    def __eq__(self, other):
        return (self.id == other.id) and (self.skill_name == other.skill_name)


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id = Column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id = Column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    level = Column(Integer, default=0)


class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    preference_type = Column(String, nullable=False)  # e.g., 'communication_style', 'interests', 'goals'
    preference_key = Column(String, nullable=False)    # Specific preference name
    preference_value = Column(JSON, nullable=False)    # The actual preference value
    confidence = Column(Float, default=1.0)           # Confidence score (0-1)
    last_updated = Column(
        Date, default=datetime.datetime.now().date(), onupdate=datetime.datetime.now().date()
    )
    
    # Add a composite unique constraint on user_id, preference_type, and preference_key
    __table_args__ = (
        UniqueConstraint('user_id', 'preference_type', 'preference_key'),
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return (
            f"<UserPreference(user_id={self.user_id}, type={self.preference_type}, "
            f"key={self.preference_key}, value={self.preference_value})>"
        )


class Training(Base):
    __tablename__ = "training"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id = Column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    status = Column(String, default="pending")
    progress = Column(Float, default=0.0)
    started_at = Column(Date, default=datetime.datetime.now().date())
    completed_at = Column(Date, default=None)
    notes = Column(String, default=None)

    def __repr__(self):
        return (
            f"<Training(user_id={self.user_id}, skill_id={self.skill_id}, "
            f"status={self.status}, progress={self.progress})>"
        )

    def __str__(self):
        return (
            f"Training for user {self.user_id} on skill {self.skill_id}: "
            f"{self.status} ({self.progress}%)"
        )

    def __eq__(self, other):
        if not isinstance(other, Training):
            return False
        return (
            self.user_id == other.user_id
            and self.skill_id == other.skill_id
            and self.status == other.status
            and self.progress == other.progress
        )


class DataModel:

    def __init__(self, sqlite_file_name="data.sqlite.db"):
        self.sqlite_file_name = sqlite_file_name
        self.sqlite_url = f"sqlite:///{self.sqlite_file_name}"
        self.engine = create_engine(self.sqlite_url, echo=False, future=True)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_db_and_tables(self):
        Base.metadata.create_all(self.engine)

    def get_db(self) -> Generator:
        """Yield a database session and ensure it's closed after use."""
        db_session = self.SessionLocal()
        try:
            yield db_session
        finally:
            db_session.close()


if __name__ == "__main__":
    # Example usage:
    data = DataModel()
    print(f"Initializing database at {data.sqlite_url}...")
    if path.exists(data.sqlite_url):
        print("Database already exists, skipping...")
    else:
        data.create_db_and_tables()
        print("Database created.")
