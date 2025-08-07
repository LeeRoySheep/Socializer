from typing import List, Optional, Any

from sqlalchemy import select, create_engine
from sqlalchemy.orm.session import sessionmaker

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

            self.engine = create_engine(
                sqlite_url, echo=True
            )  # Added 'echo' for logging during development
            self.sessionlocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )

            Base.metadata.create_all(bind=self.engine)  # Use the imported Base
        else:
            self.engine = self.data_model.engine
            self.sessionlocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )

    def get_db_session(self):
        """Factory method to get a database session."""
        session = self.sessionlocal()
        try:

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
            return (
                session.execute(select(User).where(User.username == new_user.username))
                .scalars()
                .first()
            )
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

    def update_user(self, user_id: int, **kwargs: dict[str, Any]) -> Optional[User]:
        """Update a user's information.

        Args:
            user_id: The user ID to update
            **kwargs: Keyword arguments for fields to update

        Returns:
            Updated User object if successful, None otherwise
            :rtype: Optional[User]
        """
        session = next(self.get_db_session())
        try:
            db_user = (
                session.execute(select(User).where(User.id == user_id))
                .scalars()
                .first()
            )
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
            db_user = (
                session.execute(select(User).where(User.id == user_id))
                .scalars()
                .first()
            )
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
        session = next(self.get_db_session())
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

    # Skills Management Methods

    def add_skill(self, skill: Skill) -> Optional[Skill]:
        """Add a new skill to the database.

        Args:
            skill: The Skill object to add

        Returns:
            The added Skill object if successful, None otherwise
        """
        session = next(self.get_db_session())
        if (
            not session.execute(
                select(Skill).where(Skill.skill_name == skill.skill_name)
            )
            .scalars()
            .first()
        ):
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
            return skill

    def get_skill_ids_for_user(self, user_id: int) -> List[int]:
        """Get all skill ids for a user.

        Args:
            user_id: User ID to get skills for

        Returns:
            List of Skill objects
        """
        session = next(self.get_db_session())
        statement = select(UserSkill.skill_id).where(UserSkill.user_id == user_id)
        try:
            skills = session.execute(statement).scalars().all()
            return skills
        except Exception as e:
            print(f"Error getting skills for user: {e}")
            return []

    def get_skills_for_user(self, user_id: int) -> List[Skill] | None:
        """Get all skills for a user."""
        skill_ids = self.get_skill_ids_for_user(user_id)
        if skill_ids:
            session = next(self.get_db_session())
            statement = select(Skill).where(Skill.id.in_(skill_ids))
            try:
                skills = session.execute(statement).scalars().all()
                return skills
            except Exception as e:
                print(f"Error getting skills for user: {e}")
                return None
        else:
            return []

    def get_skilllevel_for_user(self, user_id: int, skill_id: int) -> int | None:
        """Get skilllevel for a user."""
        session = next(self.get_db_session())
        skill_level = (
            session.execute(
                select(UserSkill.level).where(
                    UserSkill.user_id == user_id, UserSkill.skill_id == skill_id
                )
            )
            .scalars()
            .first()
        )
        if skill_level:
            return skill_level
        else:
            return None

    def set_skill_for_user(
        self, user_id: int, skill: Skill, level=0
    ) -> Optional[Skill]:
        """Set a skill for a user."""
        skill = self.get_or_create_skill(skill.skill_name)
        session = next(self.get_db_session())
        existing_user_skill = (
            session.execute(
                select(UserSkill).where(
                    UserSkill.user_id == user_id, UserSkill.skill_id == skill.id
                )
            )
            .scalars()
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

    def get_or_create_skill(self, skill_name: str) -> Skill | None:
        session = next(self.get_db_session())
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
                return (
                    session.query(Skill).filter(Skill.skill_name == skill_name).first()
                )
            except Exception as e:
                print(f"Error creating new skill: {e}")
                session.rollback()
                return None

    def link_user_skill(self, user_id: int, skill_id: int, level: int = 0):
        session = next(self.get_db_session())
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

    def update_training_status(
        self, user_id: int, skill_id: int, status: str
    ) -> Optional[Training]:
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
                Training.user_id == user_id, Training.skill_id == skill_id
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
