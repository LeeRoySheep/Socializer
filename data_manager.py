from contextlib import closing

import jwt


from data_model import DataModel

from sqlmodel import create_engine, select, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

data = DataModel()
data.get_session()

class DataManager:
    def __init__(self, db_path=None):
        self.data = data

        if db_path is not None:
            connect_args = {"check_same_thread": False}
            sqlite_url = f"sqlite:///{db_path}"

            engine = create_engine(sqlite_url, echo=True)  # Added 'echo' for logging during development
            sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

            DataModel.Base.metadata.create_all(bind=engine)  # Assuming ORM setup with Base defined in data_model

        def get_db_session(self):
            """Factory method to get a database session."""
            if not hasattr(DataManager, 'session_engine'):
                raise RuntimeError("Database engine must be initialized first. Call init_db_engine or pass db_path.")
            try:
                with closing(sessionlocal()) as session:
                    yield session
            except Exception as e:
                session.rollback()
                print(f"Error in database transaction: {e}")
                raise

        def add_user(self, new_user):
            """
            Add a new user to the database.
            :param new_user: The new user to add.
            """
            with self.get_db_session() as session:
                try:
                    # Check if the provided argument matches the expected model
                    if not isinstance(new_user, DataModel.User):
                        raise ValueError("new_user must be an instance of DataModel.User")

                    session.add(new_user)
                    session.commit()
                except Exception as e:
                    print(f"Error adding user: {e}")
                    session.rollback()

        def add_skills(self, new_skills: [str], username: str, session: Session):
            """ Add new skills to a user in the database.
            :param new_skills: The new skills to add.
            :param username: The id of the user.
            """
            statement = select(DataModel.User).where(DataModel.User.username == username)
            try:
                with closing(session) as session:
                    session.execute(statement).update(new_skills)
                    session.commit()
                    print(f"Added {new_skills} to {username}")
            except Exception as e:
                print(f"Error adding skills: {e}")
                session.rollback()

        def add_trainings(self, new_trainings: [str], username: str, session: Session):
            """ Add new trainings to a user in the database.
            :param new_trainings: The new trainings to add.
            :param username: The id of the user.
                """
            statement = select(DataModel.User).where(DataModel.User.username == username)
            try:
                with closing(session) as session:
                    session.execute(statement).update(new_trainings)
                    session.commit()
                    print(f"Added {new_trainings} to {username}")
            except Exception as e:
                print(f"Error adding trainings: {e}")


        ## Getter methods for all table contents ##
        # user by id
        def get_user(self, user_id: int, session: Session):
            """Get a user by their ID."""
            statement = select(DataModel.User).where(DataModel.User.id == user_id)
            try:
                return Session.exec(statement).first()
            except Exception as e:
                return f"Error fetching user: {e}"

        # user by username
        def get_user_by_username(self, username: str, session: Session):
            """Get a user by their username."""
            statement = select(self.User).where(self.User.username == username)
            try:
                return session.exec(statement).first()
            except Exception as e:
                return f"Error getting user: {e}"

        # skills for user
        def get_skills_for_user(self, user_id: int, session: Session):
            """Get all skills for a user.
            :param user_id: User ID.
            :param session: Session.
            :return: List of skills."""
            statement = select(self.Skill).where(self.Skill.user_id == user_id)
            try:
                return session.exec(statement).all()
            except Exception as e:
                return f"Error getting skills for user: {e}"

        # training for a user
        def get_training_for_user(self, user_id: int, session: Session):
            """Get training data for a user.
            :param user_id: User ID.
            :param session: Session.
            :return: Training data.
            """
            statement = select(self.Training).where(self.Training.user_id == user_id)
            try:
                return session.exec(statement).all()
            except Exception as e:
                return f"Error getting training data for user: {e}"

        # training for a skill
        def get_training_for_skill(self, skill_id: int, session: Session):
            """Get training data for a skill.
            :param skill_id: Skill ID.
            :param session: Session.
            :return: Training data.
            """
            statement = select(self.Training).where(self.Training.skill_id == skill_id)
            try:
                return session.exec(statement).all()
            except Exception as e:
                return f"Error getting training data for skill: {e}"


        @jwt.PyJWT
        def update_user(self, user_id, **kwargs):
            """Update a user's information."""
            with self.get_db_session() as session:
                try:
                    db_user = session.exec(select(DataModel.User).where(DataModel.User.id == user_id)).first()
                    if not db_user:
                        print(f"User {user_id} not found.")
                        return None
                    for key, value in kwargs.items():
                        setattr(db_user, key, value)
                    session.commit()
                except Exception as e:
                    session.rollback()
                    print(f"Error updating user: {e}")
                    raise

        def delete_user(self, user_id):
            """Delete a user by ID."""
            with self.get_db_session() as session:
                try:
                    db_user = session.exec(select(DataModel.User).where(DataModel.User.id == user_id)).first()
                    if not db_user:
                        print(f"User {user_id} not found.")
                        return False
                    session.delete(db_user)
                    session.commit()
                    return True
                except Exception as e:
                    session.rollback()
                    print(f"Error deleting user: {e}")
                    raise

        def add_other_table_data(self, table_name, **data):
            """Placeholder for adding data to other tables. Replace with actual implementation."""
            # This is where you'd implement CRUD operations for other tables.
            pass

