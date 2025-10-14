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
    DateTime,
    ForeignKey,
    create_engine,
    UniqueConstraint,
    text,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

# Define Base for SQLAlchemy ORM first
class Base(DeclarativeBase):
    pass

class TokenBlacklist(Base):
    """Model for storing blacklisted JWT tokens."""
    __tablename__ = "token_blacklist"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Relationship with User
    user: Mapped[Optional["User"]] = relationship("User", back_populates="blacklisted_tokens")
    
    def __repr__(self) -> str:
        return f"<TokenBlacklist(id={self.id}, expires_at={self.expires_at})>"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # User account status
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
    error_logs: Mapped[list["ErrorLog"]] = relationship(
        "ErrorLog", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Relationship with blacklisted tokens
    blacklisted_tokens: Mapped[list["TokenBlacklist"]] = relationship(
        "TokenBlacklist",
        back_populates="user",
        cascade="all, delete-orphan"
    )

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


class ErrorLog(Base):
    """Model for tracking errors in the application."""
    __tablename__ = "error_logs"
    
    # Maximum length for error_type field
    ERROR_TYPE_MAX_LENGTH = 100
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    error_type: Mapped[str] = mapped_column(String(ERROR_TYPE_MAX_LENGTH), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    def __init__(self, **kwargs):
        # Truncate error_type if it exceeds the maximum length
        if 'error_type' in kwargs and len(kwargs['error_type']) > self.ERROR_TYPE_MAX_LENGTH:
            kwargs['error_type'] = kwargs['error_type'][:self.ERROR_TYPE_MAX_LENGTH]
        super().__init__(**kwargs)
    
    # Relationship to User (optional)
    user: Mapped[Optional["User"]] = relationship("User", back_populates="error_logs")
    
    def __repr__(self):
        return f"<ErrorLog(id={self.id}, error_type='{self.error_type}', timestamp={self.timestamp})>"
    
    def to_dict(self):
        """Convert the ErrorLog object to a dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "context": self.context
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


class ChatRoom(Base):
    """
    Private chat room that can contain multiple users + AI.
    Supports both 1-on-1 and group conversations.
    """
    __tablename__ = "chat_rooms"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Optional custom name
    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    room_type: Mapped[str] = mapped_column(String, default="group", nullable=False)  # 'direct', 'group', 'private'
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    password: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Optional password for room protection
    
    # Relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[creator_id])
    members: Mapped[list["RoomMember"]] = relationship(
        "RoomMember", 
        back_populates="room",
        cascade="all, delete-orphan"
    )
    messages: Mapped[list["RoomMessage"]] = relationship(
        "RoomMessage",
        back_populates="room",
        cascade="all, delete-orphan",
        order_by="RoomMessage.created_at"
    )
    invites: Mapped[list["RoomInvite"]] = relationship(
        "RoomInvite",
        back_populates="room",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ChatRoom(id={self.id}, name={self.name}, creator_id={self.creator_id})>"
    
    def get_auto_name(self, db_session) -> str:
        """
        Generate automatic room name based on members.
        Returns: "Chat with Alice, Bob" or "Chat with Alice" for 1-on-1
        """
        active_members = [m for m in self.members if m.is_active and m.role != 'ai']
        member_names = []
        for member in active_members:
            if member.user_id != self.creator_id:
                user = db_session.query(User).filter(User.id == member.user_id).first()
                if user:
                    member_names.append(user.username)
        
        if not member_names:
            return "Private Room"
        return f"Chat with {', '.join(member_names)}"


class RoomMember(Base):
    """
    Association table tracking which users are members of which rooms.
    """
    __tablename__ = "room_members"
    __table_args__ = (
        UniqueConstraint('room_id', 'user_id', name='_room_user_uc'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for AI
    joined_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    role: Mapped[str] = mapped_column(String, default="member", nullable=False)  # 'creator', 'member', 'ai'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_read_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    room: Mapped["ChatRoom"] = relationship("ChatRoom", back_populates="members")
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self) -> str:
        return f"<RoomMember(room_id={self.room_id}, user_id={self.user_id}, role={self.role})>"


class RoomMessage(Base):
    """
    Messages sent in private chat rooms.
    """
    __tablename__ = "room_messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    sender_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for AI
    sender_type: Mapped[str] = mapped_column(String, default="user", nullable=False)  # 'user', 'ai', 'system'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String, default="text", nullable=False)  # 'text', 'invite', 'system'
    message_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # For invite buttons, etc.
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False, index=True
    )
    edited_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    room: Mapped["ChatRoom"] = relationship("ChatRoom", back_populates="messages")
    sender: Mapped[Optional["User"]] = relationship("User", foreign_keys=[sender_id])
    
    def __repr__(self) -> str:
        return f"<RoomMessage(id={self.id}, room_id={self.room_id}, sender_type={self.sender_type})>"


class RoomInvite(Base):
    """
    Invitations to join private chat rooms.
    Appears as a message in the invitee's main chat.
    """
    __tablename__ = "room_invites"
    __table_args__ = (
        UniqueConstraint('room_id', 'invitee_id', name='_room_invitee_uc'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    inviter_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    invitee_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)  # 'pending', 'accepted', 'declined'
    message_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("room_messages.id"), nullable=True
    )  # Reference to invite message shown in main chat
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    responded_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    room: Mapped["ChatRoom"] = relationship("ChatRoom", back_populates="invites")
    inviter: Mapped["User"] = relationship("User", foreign_keys=[inviter_id])
    invitee: Mapped["User"] = relationship("User", foreign_keys=[invitee_id])
    
    def __repr__(self) -> str:
        return f"<RoomInvite(id={self.id}, room_id={self.room_id}, invitee_id={self.invitee_id}, status={self.status})>"


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
