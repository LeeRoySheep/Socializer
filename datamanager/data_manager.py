import datetime
import json
from typing import List, Optional, Any
from contextlib import contextmanager

# Import models from parent directory
from datamanager.data_model import (
    User, Skill, Training, DataModel, UserSkill, UserPreference,
    ChatRoom, RoomMember, RoomMessage, RoomInvite
)


class DataManager:
    @contextmanager
    def get_session(self):
        """Context manager for database sessions that ensures proper cleanup.
        
        Usage:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                return user
        """
        session = self.data_model.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # User Preference Methods
    
    def get_user_preferences(self, user_id: int, preference_type: str = None) -> dict:
        """
        Get all preferences for a user, optionally filtered by preference type.
        
        Args:
            user_id: The ID of the user
            preference_type: Optional type filter for preferences
            
        Returns:
            Dictionary of preferences with keys as preference keys and values as preference values
        """
        with self.get_session() as session:
            try:
                query = session.query(UserPreference).filter(UserPreference.user_id == user_id)
                if preference_type:
                    query = query.filter(UserPreference.preference_type == preference_type)
                    
                preferences = query.all()
                return {
                    f"{pref.preference_type}.{pref.preference_key}": pref.preference_value
                    for pref in preferences
                }
            except Exception as e:
                print(f"Error getting user preferences: {e}")
                return {}
    
    def set_user_preference(
        self, 
        user_id: int, 
        preference_type: str, 
        preference_key: str, 
        preference_value: Any,
        confidence: float = 1.0
    ) -> bool:
        """
        Set or update a user preference.
        
        Args:
            user_id: The ID of the user
            preference_type: Category/type of the preference (e.g., 'communication_style')
            preference_key: Specific preference name
            preference_value: The preference value (will be stored as JSON)
            confidence: Confidence score (0-1) for this preference
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.get_session() as session:
            try:
                # Check if preference already exists
                pref = session.query(UserPreference).filter(
                    UserPreference.user_id == user_id,
                    UserPreference.preference_type == preference_type,
                    UserPreference.preference_key == preference_key
                ).first()
                
                if pref:
                    # Update existing preference
                    pref.preference_value = preference_value
                    pref.confidence = confidence
                    pref.last_updated = datetime.datetime.now().date()
                else:
                    # Create new preference
                    pref = UserPreference(
                        user_id=user_id,
                        preference_type=preference_type,
                        preference_key=preference_key,
                        preference_value=preference_value,
                        confidence=confidence,
                        last_updated=datetime.datetime.now().date()
                    )
                    session.add(pref)
                
                session.commit()
                return True
                    
            except Exception as e:
                session.rollback()
                print(f"Error setting user preference: {e}")
                return False
    
    def delete_user_preference(
        self, 
        user_id: int, 
        preference_type: str = None, 
        preference_key: str = None
    ) -> bool:
        """
        Delete user preferences matching the criteria.
        
        Args:
            user_id: The ID of the user
            preference_type: Optional type filter for preferences to delete
            preference_key: Optional key filter for preferences to delete
            
        Returns:
            bool: True if any preferences were deleted, False otherwise
        """
        with self.get_session() as session:
            try:
                query = session.query(UserPreference).filter(
                    UserPreference.user_id == user_id
                )
                
                if preference_type:
                    query = query.filter(UserPreference.preference_type == preference_type)
                if preference_key:
                    query = query.filter(UserPreference.preference_key == preference_key)
                
                deleted_count = query.delete()
                session.commit()
                return deleted_count > 0
                    
            except Exception as e:
                session.rollback()
                print(f"Error deleting user preferences: {e}")
                return False

    def __init__(self, db_path=None):
        """Initialize the DataManager with an optional database path.

        Args:
            db_path: Path to the SQLite database file. If None, uses the DataModel default.
        """
        if db_path is not None:
            self.data_model = DataModel(sqlite_file_name=db_path)
            self.data_model.create_db_and_tables()
        else:
            self.data_model = DataModel()
            self.data_model.create_db_and_tables()

    # User Management Methods

    def add_user(self, new_user: User) -> Optional[User]:
        """Add a new user to the database.

        Args:
            new_user: The User object to add

        Returns:
            The added User object if successful, None otherwise
        """
        with self.get_session() as session:
            try:
                # Check if the provided argument matches the expected model
                if not isinstance(new_user, User):
                    raise ValueError("new_user must be an instance of User")
                if session.query(User).filter(User.username == new_user.username).first():
                    print(f"User with username {new_user.username} already exists.")
                    return None
                session.add(new_user)
                session.commit()
                session.refresh(new_user)
                return new_user
            except Exception as e:
                print(f"Error adding user: {e}")
                session.rollback()
                return None

    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by their ID.

        Args:
            user_id: The user ID to look up

        Returns:
            User object if found, None otherwise
        """
        with self.get_session() as session:
            try:
                return session.query(User).filter(User.id == user_id).first()
            except Exception as e:
                print(f"Error fetching user: {e}")
                return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by their username.

        Args:
            username: The username to look up

        Returns:
            User object if found, None otherwise
        """
        with self.get_session() as session:
            try:
                return session.query(User).filter(User.username == username).first()
            except Exception as e:
                print(f"Error getting user: {e}")
                return None

    def update_user(self, user_id: int, **kwargs: dict[str, Any]) -> Optional[User]:
        """Update a user's information.

        Args:
            user_id: The user ID to update
            **kwargs: Keyword arguments for fields to update

        Returns:
            Updated User object if successful, None otherwise
            :rtype: Optional[User]
        """
        with self.get_session() as session:
            try:
                db_user = session.query(User).filter(User.id == user_id).first()
                if not db_user:
                    print(f"User {user_id} not found.")
                    return None

                for key, value in kwargs.items():
                    setattr(db_user, key, value)

                session.commit()
                session.refresh(db_user)
                return db_user
            except Exception as e:
                session.rollback()
                print(f"Error updating user: {e}")
                return None

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID.

        Args:
            user_id: The user ID to delete

        Returns:
            True if successful, False otherwise
        """
        with self.get_session() as session:
            try:
                db_user = session.query(User).filter(User.id == user_id).first()
                if not db_user:
                    print(f"User {user_id} not found.")
                    return False

                session.delete(db_user)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Error deleting user: {e}")
                return False

    def set_user_temperature(self, user_id: int, temperature: float) -> None:
        """Set a user's temperature.
        Args:
            user_id: The user ID to set
            temperature: The new temperature
        Returns:
            None
        """
        with self.get_session() as session:
            try:
                # Use the ORM to update the user's temperature
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    user.temperature = temperature
                    session.commit()
                    print("User temperature set successfully!")
                else:
                    print(f"User with ID {user_id} not found.")
            except Exception as e:
                session.rollback()
                print(f"Error setting user's temperature: {e}")

    def save_messages(self, user_id: int, messages: list) -> None:
        with self.get_session() as session:
            try:
                # Get the user with the current session to ensure it's attached
                user = session.query(User).filter(User.id == user_id).with_for_update().first()
                if user is None:
                    print(f"User with ID {user_id} not found.")
                    return None

                # Extract only content and role from messages
                serializable_messages = []
                for msg in messages:
                    if hasattr(msg, "dict"):  # For Pydantic models
                        msg_dict = msg.dict()
                    elif isinstance(msg, dict):
                        msg_dict = msg
                    else:
                        print(f"Skipping invalid message format: {msg}")
                        continue  # Skip invalid message formats
                    
                    # Only keep content and role
                    filtered_msg = {
                        'content': str(msg_dict.get('content', '')),  # Ensure content is string
                        'role': str(msg_dict.get('role', 'user'))  # Default to 'user' if role not specified
                    }
                    serializable_messages.append(filtered_msg)

                if not serializable_messages:
                    print("No valid messages to save")
                    return None

                # Initialize or update messages
                existing_messages = []
                if user.messages:
                    try:
                        # If messages is a string, parse it as JSON
                        if isinstance(user.messages, str):
                            existing_messages = json.loads(user.messages)
                        # If it's already a list, use it directly
                        elif isinstance(user.messages, list):
                            existing_messages = user.messages
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"Error parsing existing messages: {e}")
                        existing_messages = []

                # Ensure we're working with lists
                if not isinstance(existing_messages, list):
                    if isinstance(existing_messages, str):
                        try:
                            existing_messages = json.loads(existing_messages)
                        except json.JSONDecodeError:
                            existing_messages = []
                    else:
                        existing_messages = []
                
                # Only keep the last message from existing messages to maintain context
                last_existing = existing_messages[-1:] if existing_messages else []
                
                # Ensure serializable_messages is a list
                if not isinstance(serializable_messages, list):
                    serializable_messages = []
                
                # Combine last existing message with new messages and keep last 10
                updated_messages = last_existing + serializable_messages[-10:]
                
                # Store as JSON string
                user.messages = json.dumps(updated_messages, ensure_ascii=False)
                
                # Explicitly mark as modified
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(user, 'messages')
                
                # Add and commit in the same transaction
                session.add(user)
                session.commit()
                
            except Exception as e:
                session.rollback()
                print(f"Error saving user messages: {e}")
                raise

    # Skills Management Methods

    def add_skill(self, skill: Skill) -> Optional[Skill]:
        """Add a new skill to the database.

        Args:
            skill: The Skill object to add

        Returns:
            The added Skill object if successful, None otherwise
        """
        with self.get_session() as session:
            new_skill = session.query(Skill).filter(Skill.id == skill.id).first()
            if not new_skill:
                try:
                    session.add(skill)
                    session.commit()
                    session.refresh(skill)
                    return skill
                except Exception as e:
                    session.rollback()
                    print(f"Error adding skill: {e}")
                    return None
            else:
                print(f"Skill with ID {skill.id} already exists.")
                return None

    def get_skill_ids_for_user(self, user_id: int) -> List[int]:
        """Get all skill ids for a user.

        Args:
            user_id: User ID to get skills for

        Returns:
            List of Skill objects
        """
        with self.get_session() as session:
            try:
                skill_ids = (
                    session.query(UserSkill.skill_id)
                    .filter(UserSkill.user_id == user_id)
                    .all()
                )
                return [skill_id for (skill_id,) in skill_ids]
            except Exception as e:
                print(f"Error getting skills for user: {e}")
                return []

    def get_skills_for_user(self, user_id: int) -> Optional[List[Skill]]:
        """Get all skills for a user."""
        skill_ids = self.get_skill_ids_for_user(user_id)
        if skill_ids:
            with self.get_session() as session:
                try:
                    skills = [
                        session.query(Skill).filter(Skill.id == skill_id).first()
                        for skill_id in skill_ids
                    ]
                    return skills
                except Exception as e:
                    print(f"Error getting skills for user: {e}")
                    return None
        else:
            print("No skills found.")
            return None

    def get_skilllevel_for_user(self, user_id: int, skill_id: int) -> Optional[int]:
        """Get skilllevel for a user."""
        with self.get_session() as session:
            skill_level = (
                session.query(UserSkill.level)
                .filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id)
                .first()
            )
            if skill_level and skill_level[0] is not None:
                return skill_level[0]  # Return just the level value
            else:
                return 0  # Default to 0 if no skill level found

    def set_skill_for_user(
        self, user_id: int, skill: Skill, level=0
    ) -> Optional[Skill]:
        """Set a skill for a user."""
        skill = self.get_or_create_skill(skill.skill_name)
        with self.get_session() as session:
            existing_user_skill = (
                session.query(UserSkill)
                .filter_by(user_id=user_id, skill_id=skill.id)
                .first()
            )
            # Checking if user already set to skill and overwriting db entry if found
            if existing_user_skill:
                try:
                    existing_user_skill.level = level
                    session.commit()
                    return skill
                except Exception as e:
                    print(f"Error updating skill for user: {e}")
                    session.rollback()
                    return None
            # connecting user to skill
            try:
                new_skill = self.get_or_create_skill(skill.skill_name)
                session.add(UserSkill(user_id=user_id, skill_id=new_skill.id, level=level))
                session.commit()
                return new_skill
            except Exception as e:
                print(f"Error setting skill for user: {e}")
                session.rollback()
                return None

    # In DataManager class:

    def get_or_create_skill(self, skill_name: str) -> Optional[Skill]:
        with self.get_session() as session:
            skill = session.query(Skill).filter(Skill.skill_name == skill_name).first()
            if skill:
                print("Skill already exists.")
                return skill
            else:
                new_skill = Skill(skill_name=skill_name)
                try:
                    session.add(new_skill)
                    session.commit()
                    session.refresh(new_skill)
                    return new_skill
                except Exception as e:
                    print(f"Error creating new skill: {e}")
                    session.rollback()
                    return None

    def link_user_skill(self, user_id: int, skill_id: int, level: int = 0):
        with self.get_session() as session:
            existing = (
                session.query(UserSkill)
                .filter_by(user_id=user_id, skill_id=skill_id)
                .first()
            )
            if not existing:
                userskill = UserSkill(user_id=user_id, skill_id=skill_id, level=level)
                try:
                    session.add(userskill)
                    session.commit()
                except Exception as e:
                    print(f"Error adding userskill: {e}")
                    session.rollback()

    # Training Management Methods

    def add_training(self, training: Training) -> Optional[Training]:
        """Add a new training record.

        Args:
            training: The Training object to add

        Returns:
            The added Training object if successful, None otherwise
        """
        with self.get_session() as session:
            try:
                session.add(training)
                session.commit()
                session.refresh(training)

                return training
            except Exception as e:
                session.rollback()
                print(f"Error adding training: {e}")
                return None

    def get_training_for_user(self, user_id: int) -> List[Training]:
        """Get training data for a user.

        Args:
            user_id: User ID to get training for

        Returns:
            List of Training objects
        """
        with self.get_session() as session:
            try:
                return session.query(Training).filter(Training.user_id == user_id).all()
            except Exception as e:
                print(f"Error getting training data for user: {e}")
                return []

    def get_training_for_skill(self, skill_id: int) -> List[Training]:
        """Get training data for a skill.

        Args:
            skill_id: Skill ID to get training for

        Returns:
            List of Training objects
        """
        with self.get_session() as session:
            try:
                return session.query(Training).filter(Training.skill_id == skill_id).all()
            except Exception as e:
                print(f"Error getting training data for skill: {e}")
                return []

    def update_training_status(
        self, user_id: int, skill_id: int, new_status: str
    ) -> Optional[Training]:
        """Update a training status.

        Args:
            user_id: User ID for the training
            skill_id: Skill ID for the training
            status: New status for the training

        Returns:
            Updated Training object if successful, None otherwise
        """
        with self.get_session() as session:
            try:
                training = (
                    session.query(Training)
                    .filter(Training.user_id == user_id, Training.skill_id == skill_id)
                    .first()
                )

                if not training:
                    print(f"Training for user {user_id} and skill {skill_id} not found.")
                    return None

                setattr(training, "status", new_status)
                session.commit()
                session.refresh(training)
                return training
            except Exception as e:
                session.rollback()
                print(f"Error updating training status: {e}")
                return None

    # ==========================================
    # PRIVATE CHAT ROOM METHODS
    # ==========================================

    def create_room(
        self, 
        creator_id: int, 
        name: Optional[str] = None,
        room_type: str = "group",
        ai_enabled: bool = True,
        password: Optional[str] = None
    ) -> Optional[ChatRoom]:
        """
        Create a new chat room.
        
        Args:
            creator_id (int): ID of the user creating the room
            name (str, optional): Custom room name. Auto-generated if None
            room_type (str): 'direct' (1-on-1), 'group', or 'private'
            ai_enabled (bool): Whether AI should participate in the room
            password (str, optional): Password for room protection. None = open room
            
        Returns:
            ChatRoom: The created room, or None if error
        """
        # OBSERVABILITY: Log room creation attempt
        print(f"[TRACE] create_room: creator_id={creator_id}, name={name}, type={room_type}, ai={ai_enabled}, protected={bool(password)}")
        
        with self.get_session() as session:
            try:
                # Create room
                room = ChatRoom(
                    creator_id=creator_id,
                    name=name,
                    room_type=room_type,
                    ai_enabled=ai_enabled,
                    password=password
                )
                session.add(room)
                session.flush()  # Get room ID
                
                # Add creator as member
                creator_member = RoomMember(
                    room_id=room.id,
                    user_id=creator_id,
                    role='creator'
                )
                session.add(creator_member)
                
                # Add AI as member if enabled
                if ai_enabled:
                    ai_member = RoomMember(
                        room_id=room.id,
                        user_id=None,  # AI has no user_id
                        role='ai'
                    )
                    session.add(ai_member)
                
                session.commit()
                session.refresh(room)
                # OBSERVABILITY: Log successful creation
                print(f"[TRACE] create_room success: room_id={room.id}, members={2 if ai_enabled else 1}")
                return room
            except Exception as e:
                session.rollback()
                # OBSERVABILITY: Log error with context
                print(f"[ERROR] create_room exception: creator_id={creator_id}, error={e}")
                return None

    def get_room(self, room_id: int) -> Optional[ChatRoom]:
        """
        Get a room by ID.
        
        Args:
            room_id (int): Room ID
            
        Returns:
            ChatRoom: The room, or None if not found
        """
        with self.get_session() as session:
            try:
                room = session.query(ChatRoom).filter(ChatRoom.id == room_id).first()
                if room:
                    # Make object accessible outside session by expunging it
                    session.expunge(room)
                return room
            except Exception as e:
                print(f"Error getting room: {e}")
                return None

    def get_user_rooms(self, user_id: int) -> List[ChatRoom]:
        """
        Get all rooms where user is a member.
        
        Args:
            user_id (int): User ID
            
        Returns:
            List[ChatRoom]: List of rooms
        """
        with self.get_session() as session:
            try:
                rooms = (
                    session.query(ChatRoom)
                    .join(RoomMember)
                    .filter(
                        RoomMember.user_id == user_id,
                        RoomMember.is_active == True,
                        ChatRoom.is_active == True
                    )
                    .order_by(ChatRoom.created_at.desc())
                    .all()
                )
                # Make objects accessible outside session
                for room in rooms:
                    session.expunge(room)
                return rooms
            except Exception as e:
                print(f"Error getting user rooms: {e}")
                return []

    def invite_user_to_room(
        self, 
        room_id: int, 
        inviter_id: int, 
        invitee_id: int
    ) -> Optional[RoomInvite]:
        """
        Invite a user to a room.
        Creates invite record and message in invitee's main chat.
        
        Args:
            room_id (int): Room ID
            inviter_id (int): ID of user sending invite
            invitee_id (int): ID of user being invited
            
        Returns:
            RoomInvite: The created invite, or None if error
        """
        with self.get_session() as session:
            try:
                # Get room and inviter info
                room = session.query(ChatRoom).filter(ChatRoom.id == room_id).first()
                inviter = session.query(User).filter(User.id == inviter_id).first()
                
                if not room or not inviter:
                    return None
                
                # Check if invite already exists
                existing = (
                    session.query(RoomInvite)
                    .filter(
                        RoomInvite.room_id == room_id,
                        RoomInvite.invitee_id == invitee_id,
                        RoomInvite.status == 'pending'
                    )
                    .first()
                )
                if existing:
                    return existing
                
                # Create invite
                invite = RoomInvite(
                    room_id=room_id,
                    inviter_id=inviter_id,
                    invitee_id=invitee_id,
                    status='pending'
                )
                session.add(invite)
                session.commit()
                session.refresh(invite)
                return invite
            except Exception as e:
                session.rollback()
                print(f"Error creating invite: {e}")
                return None

    def accept_invite(self, invite_id: int, user_id: int, password: Optional[str] = None) -> bool:
        """
        Accept a room invite.
        Adds user as room member.
        
        Args:
            invite_id (int): Invite ID
            user_id (int): ID of user accepting
            password (str, optional): Password if room is protected
            
        Returns:
            bool: True if successful, False otherwise
        """
        # OBSERVABILITY: Log invite acceptance attempt
        print(f"[TRACE] accept_invite: invite_id={invite_id}, user_id={user_id}, has_password={bool(password)}")
        
        with self.get_session() as session:
            try:
                invite = session.query(RoomInvite).filter(RoomInvite.id == invite_id).first()
                
                if not invite:
                    print(f"[EVAL] accept_invite failed: invite {invite_id} not found")
                    return False
                    
                if invite.invitee_id != user_id:
                    print(f"[EVAL] accept_invite failed: user {user_id} not the invitee (expected {invite.invitee_id})")
                    return False
                    
                if invite.status != 'pending':
                    print(f"[EVAL] accept_invite failed: invite status is '{invite.status}', expected 'pending'")
                    return False
                
                # IMPORTANT: Invited users do NOT need password!
                # Password protection only applies to uninvited users trying to join directly.
                # Since this user has a valid invite, they bypass password check.
                print(f"[TRACE] User {user_id} has valid invite - bypassing password check")
                
                # Update invite status
                invite.status = 'accepted'
                invite.responded_at = datetime.datetime.utcnow()
                
                # Add user as room member
                member = RoomMember(
                    room_id=invite.room_id,
                    user_id=user_id,
                    role='member'
                )
                session.add(member)
                
                session.commit()
                # OBSERVABILITY: Log successful acceptance
                print(f"[TRACE] accept_invite success: user {user_id} added to room {invite.room_id}")
                return True
            except Exception as e:
                session.rollback()
                # OBSERVABILITY: Log error with context
                print(f"[ERROR] accept_invite exception: invite_id={invite_id}, user_id={user_id}, error={e}")
                return False

    def decline_invite(self, invite_id: int, user_id: int) -> bool:
        """
        Decline a room invite.
        
        Args:
            invite_id (int): Invite ID
            user_id (int): ID of user declining
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.get_session() as session:
            try:
                invite = session.query(RoomInvite).filter(RoomInvite.id == invite_id).first()
                
                if not invite or invite.invitee_id != user_id or invite.status != 'pending':
                    return False
                
                invite.status = 'declined'
                invite.responded_at = datetime.datetime.utcnow()
                
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Error declining invite: {e}")
                return False

    def add_room_message(
        self,
        room_id: int,
        sender_id: Optional[int],
        content: str,
        sender_type: str = "user",
        message_type: str = "text",
        message_metadata: Optional[dict] = None
    ) -> Optional[RoomMessage]:
        """
        Add a message to a room.
        
        Args:
            room_id (int): Room ID
            sender_id (int, optional): User ID of sender (None for AI)
            content (str): Message content
            sender_type (str): 'user', 'ai', or 'system'
            message_type (str): 'text', 'invite', 'system'
            message_metadata (dict, optional): Additional data
            
        Returns:
            RoomMessage: The created message, or None if error
        """
        with self.get_session() as session:
            try:
                message = RoomMessage(
                    room_id=room_id,
                    sender_id=sender_id,
                    content=content,
                    sender_type=sender_type,
                    message_type=message_type,
                    message_metadata=message_metadata or {}
                )
                session.add(message)
                session.commit()
                session.refresh(message)
                return message
            except Exception as e:
                session.rollback()
                print(f"Error adding room message: {e}")
                return None

    def get_room_messages(
        self, 
        room_id: int, 
        limit: int = 50,
        before_id: Optional[int] = None
    ) -> List[RoomMessage]:
        """
        Get messages from a room.
        
        Args:
            room_id (int): Room ID
            limit (int): Maximum number of messages to return
            before_id (int, optional): Get messages before this message ID (for pagination)
            
        Returns:
            List[RoomMessage]: List of messages
        """
        with self.get_session() as session:
            try:
                query = (
                    session.query(RoomMessage)
                    .filter(
                        RoomMessage.room_id == room_id,
                        RoomMessage.is_deleted == False
                    )
                )
                
                if before_id:
                    query = query.filter(RoomMessage.id < before_id)
                
                messages = (
                    query
                    .order_by(RoomMessage.created_at.desc())
                    .limit(limit)
                    .all()
                )
                # Make objects accessible outside session
                for msg in messages:
                    session.expunge(msg)
                return list(reversed(messages))  # Return in chronological order
            except Exception as e:
                print(f"Error getting room messages: {e}")
                return []

    def get_room_members(self, room_id: int) -> List[RoomMember]:
        """
        Get all active members of a room.
        
        Args:
            room_id (int): Room ID
            
        Returns:
            List[RoomMember]: List of room members
        """
        with self.get_session() as session:
            try:
                members = (
                    session.query(RoomMember)
                    .filter(
                        RoomMember.room_id == room_id,
                        RoomMember.is_active == True
                    )
                    .all()
                )
                # Make objects accessible outside session
                for member in members:
                    session.expunge(member)
                return members
            except Exception as e:
                print(f"Error getting room members: {e}")
                return []

    def is_user_in_room(self, user_id: int, room_id: int) -> bool:
        """
        Check if user is a member of a room.
        
        Args:
            user_id (int): User ID
            room_id (int): Room ID
            
        Returns:
            bool: True if user is member, False otherwise
        """
        with self.get_session() as session:
            try:
                member = (
                    session.query(RoomMember)
                    .filter(
                        RoomMember.user_id == user_id,
                        RoomMember.room_id == room_id,
                        RoomMember.is_active == True
                    )
                    .first()
                )
                return member is not None
            except Exception as e:
                print(f"Error checking room membership: {e}")
                return False

    def leave_room(self, user_id: int, room_id: int) -> bool:
        """
        User leaves a room.
        
        Args:
            user_id (int): User ID
            room_id (int): Room ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.get_session() as session:
            try:
                member = (
                    session.query(RoomMember)
                    .filter(
                        RoomMember.user_id == user_id,
                        RoomMember.room_id == room_id
                    )
                    .first()
                )
                
                if not member:
                    return False
                
                member.is_active = False
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Error leaving room: {e}")
                return False

    def get_pending_invites(self, user_id: int) -> List[RoomInvite]:
        """
        Get all pending invites for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            List[RoomInvite]: List of pending invites
        """
        with self.get_session() as session:
            try:
                invites = (
                    session.query(RoomInvite)
                    .filter(
                        RoomInvite.invitee_id == user_id,
                        RoomInvite.status == 'pending'
                    )
                    .order_by(RoomInvite.created_at.desc())
                    .all()
                )
                # Make objects accessible outside session
                for invite in invites:
                    session.expunge(invite)
                return invites
            except Exception as e:
                print(f"Error getting pending invites: {e}")
                return []
