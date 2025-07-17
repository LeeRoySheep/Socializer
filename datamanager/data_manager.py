from typing import List, Optional

from sqlalchemy.orm.session import sessionmaker
from sqlmodel import select, create_engine

# Import models from parent directory
from datamanager.data_model import User, Skill, Training, DataModel, Base, UserSkill


class DataManager:
    def __init__(self, db_path=None):
        """Initialize the DataManager with an optional database path.

        Args:
            db_path: Path to the SQLite database file. If None, uses the DataModel default.
        """
        self.data_model = DataModel()

        if db_path is not None:
            connect_args = {"check_same_thread": False}
            sqlite_url = f"sqlite:///{db_path}"

            self.engine = create_engine(sqlite_url, echo=True)  # Added 'echo' for logging during development
            self.sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            Base.metadata.create_all(bind=self.engine)  # Use the imported Base
        else:
            self.engine = self.data_model.engine
            self.sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_db_session(self):
        """Factory method to get a database session."""
        try:
            session = self.sessionlocal()
            yield session
        except Exception as e:
            session.rollback()
            print(f"Error in database transaction: {e}")
            raise
        finally:
            session.close()

    # User Management Methods

    def add_user(self, new_user: User) -> Optional[User]:
        """Add a new user to the database.

        Args:
            new_user: The User object to add

        Returns:
            The added User object if successful, None otherwise
        """
        session = next(self.get_db_session())
        try:
            # Check if the provided argument matches the expected model
            if not isinstance(new_user, User):
                raise ValueError("new_user must be an instance of User")

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
        session = next(self.get_db_session())
        statement = select(User).where(User.id == user_id)
        try:
            return session.execute(statement).scalars().first()
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
        session = next(self.get_db_session())
        statement = select(User).where(User.username == username)
        try:
            return session.execute(statement).scalars().first()
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update a user's information.

        Args:
            user_id: The user ID to update
            **kwargs: Keyword arguments for fields to update

        Returns:
            Updated User object if successful, None otherwise
        """
        session = next(self.get_db_session())
        try:
            db_user = session.execute(select(User).where(User.id == user_id)).scalars().first()
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
        session = next(self.get_db_session())
        try:
            db_user = session.execute(select(User).where(User.id == user_id)).scalars().first()
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

    # Skills Management Methods

    def add_skill(self, skill: Skill) -> Optional[Skill]:
        """Add a new skill to the database.

        Args:
            skill: The Skill object to add

        Returns:
            The added Skill object if successful, None otherwise
        """
        session = next(self.get_db_session())
        try:
            session.add(skill)
            session.commit()
            session.refresh(skill)
            users = skill.user_id
            return skill
        except Exception as e:
            session.rollback()
            print(f"Error adding skill: {e}")
            return None

    def get_skills_for_user(self, user_id: int) -> List[Skill]:
        """Get all skills for a user.

        Args:
            user_id: User ID to get skills for

        Returns:
            List of Skill objects
        """
        session = next(self.get_db_session())
        statement = select(UserSkill).where(UserSkill.user_id == user_id)
        try:
            return session.execute(statement).scalars().all()
        except Exception as e:
            print(f"Error getting skills for user: {e}")
            return []

    def set_skill_for_user(self, user_id: int, skill: Skill) -> Optional[Skill]:
        """Set a skill for a user.  """
        session = next(self.get_db_session())
        try:
            session.add(UserSkill(user_id=user_id, skill_id=skill.id))
            session.commit()
            session.refresh(skill)
        except Exception as e:
            print(f"Error setting skill for user: {e}")
            session.rollback()

    # Training Management Methods

    def add_training(self, training: Training) -> Optional[Training]:
        """Add a new training record.

        Args:
            training: The Training object to add

        Returns:
            The added Training object if successful, None otherwise
        """
        session = next(self.get_db_session())
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
        session = next(self.get_db_session())
        statement = select(Training).where(Training.user_id == user_id)
        try:
            return session.execute(statement).scalars().all()
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
        session = next(self.get_db_session())
        statement = select(Training).where(Training.skill_id == skill_id)
        try:
            return session.execute(statement).scalars().all()
        except Exception as e:
            print(f"Error getting training data for skill: {e}")
            return []

    def update_training_status(self, user_id: int, skill_id: int, status: str) -> Optional[Training]:
        """Update a training status.

        Args:
            user_id: User ID for the training
            skill_id: Skill ID for the training
            status: New status for the training

        Returns:
            Updated Training object if successful, None otherwise
        """
        session = next(self.get_db_session())
        try:
            statement = select(Training).where(
                Training.user_id == user_id,
                Training.skill_id == skill_id
            )
            training = session.execute(statement).scalars().first()

            if not training:
                print(f"Training for user {user_id} and skill {skill_id} not found.")
                return None

            training.status = status
            if status == "completed":
                training.absolved = True

            session.add(training)
            session.commit()
            session.refresh(training)
            return training
        except Exception as e:
            session.rollback()
            print(f"Error updating training status: {e}")
            return None
