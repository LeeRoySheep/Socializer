import os
import sys
import unittest
from datetime import datetime

# Make sure we can import from parent directory
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlmodel import Session, create_engine, SQLModel

from datamanager.data_model import User, Skill, Training
from datamanager.data_manager import DataManager

# Define a test database path
TEST_DB_PATH = "test_users_data.db"


class TestDataModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Remove old test database if it exists
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

        # Create engine and tables directly
        sqlite_url = f"sqlite:///{TEST_DB_PATH}"
        connect_args = {"check_same_thread": False}
        cls.engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

        # Create all tables
        SQLModel.metadata.create_all(cls.engine)

        # Create a data manager for testing
        cls.data_manager = DataManager(db_path=TEST_DB_PATH)

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests are done."""
        # Close the engine
        cls.engine.dispose()

        # Remove the test database file
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def setUp(self):
        """Set up before each test."""
        # Create a new session for each test
        self.session = Session(self.engine)

        # Clear all data before each test
        self.session.execute("DELETE FROM training")
        self.session.execute("DELETE FROM skill")
        self.session.execute("DELETE FROM user")
        self.session.commit()

    def tearDown(self):
        """Clean up after each test."""
        # Close the session
        self.session.close()

    def test_create_user(self):
        """Test creating a user."""
        # Create a test user
        user = User(
            username="test_user", hashed_password="hashed_password", role="user"
        )

        # Add the user using the data manager
        added_user = self.data_manager.add_user(user)

        # Verify the user was added
        self.assertIsNotNone(added_user)
        self.assertEqual(added_user.username, "test_user")

        # Verify the user can be retrieved
        retrieved_user = self.data_manager.get_user_by_username("test_user")
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, "test_user")

    def test_user_skills(self):
        """Test that skills are properly stored and retrieved."""
        # Create a test user
        user = User(
            username="skill_test_user",
            hashed_password="hashed_password",
            hashed_email="hashed_email",
            role="user",
        )

        # data manager
        data = self.data_manager

        # Add the user
        added_user = data.add_user(user)

        # Test getting empty skills list
        skills = data.get_skills_for_user(added_user.id)
        self.assertEqual(skills, [])

        # Test setting skills list
        test_skill = data.get_or_create_skill("Python")
        data.set_skill_for_user(added_user.id, test_skill, 3)
        test_skill_2 = data.get_or_create_skill("JavaScript")
        data.set_skill_for_user(added_user.id, test_skill_2, 2)
        skills = data.get_skills_for_user(added_user.id)
        self.assertEqual(skills, [test_skill, test_skill_2])

        # Update the user
        data.update_user(
            added_user.id,
            **{"hashed_password": "<NEWPASSWORD>", "hashed_email": "<EMAIL>"},
        )

        # Retrieve the user again
        retrieved_user = data.get_user(added_user.id)

        # Verify skills were saved properly
        retrieved_skills = data.get_skills_for_user(retrieved_user.id)
        self.assertEqual(retrieved_skills, [test_skill, test_skill_2])

    def test_add_skill(self):
        """Test adding a skill to a user."""
        # Create a test user
        user = User(
            username="skill_user",
            hashed_password="hashed_password",
            role="user",
        )
        added_user = self.data_manager.add_user(user)

        # Create a skill for the user
        skill = Skill(skill_name="Python")

        # Add the skill
        added_skill = self.data_manager.set_skill_for_user(
            added_user.id, skill, level=3
        )
        self.assertIsNotNone(added_skill)
        self.assertEqual(added_skill.skill_name, "Python")

        # Verify the skill is linked to the user
        skills = self.data_manager.get_skills_for_user(added_user.id)
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].skill_name, "Python")

        # Verify user has the skill in their list
        updated_user = self.data_manager.update_user(
            added_user.id, hashed_password="<PASSWORD>"
        )
        self.assertIsNotNone(updated_user)
        user_skills = self.data_manager.get_skills_for_user(updated_user.id)
        self.assertIn(added_skill, user_skills)

    def test_add_training(self):
        """Test adding a training session."""
        # Create a test user
        user = User(
            username="training_user",
            hashed_password="hashed_password",
            role="user",
        )
        added_user = self.data_manager.add_user(user)

        # Create a skill for the user
        skill = Skill(user_id=added_user.id, skill_name="JavaScript", level=2)
        added_skill = self.data_manager.add_skill(skill)

        # Create a training for the skill
        training = Training(
            user_id=added_user.id,
            skill_id=added_skill.id,
            body="Learning JavaScript fundamentals",
            status="pending",
            started_at=datetime.now().date(),
        )

        # Add the training
        added_training = self.data_manager.add_training(training)
        self.assertIsNotNone(added_training)
        self.assertEqual(added_training.body, "Learning JavaScript fundamentals")

        # Verify the training is associated with the user
        trainings = self.data_manager.get_training_for_user(added_user.id)
        self.assertEqual(len(trainings), 1)

        # Verify the training is associated with the skill
        skill_trainings = self.data_manager.get_training_for_skill(added_skill.id)
        self.assertEqual(len(skill_trainings), 1)

        # Check that the user's trainings list was updated
        updated_user = self.data_manager.update_user(added_user.id, **{"role": "admin"})
        self.assertIsNotNone(updated_user)
        user_trainings = self.data_manager.get_training_for_user(updated_user.id)
        self.assertIn(added_training, user_trainings)

    def test_update_training_status(self):
        """Test updating a training status."""
        # Create a test user
        user = User(
            username="training_user", hashed_password="hashed_password", role="user"
        )
        added_user = self.data_manager.add_user(user)

        # Create a skill for the user
        skill = Skill(user_id=added_user.id, skill_name="JavaScript")
        added_skill = self.data_manager.set_skill_for_user(added_user.id, skill, 2)
        # Create a training for the skill
        training = Training(
            user_id=added_user.id,
            skill_id=added_skill.id,
            body="Learning JavaScript fundamentals",
            status="pending",
            started_at=datetime.now().date(),
        )
        added_training = self.data_manager.add_training(training)
        self.assertIsNotNone(added_training)
        self.assertEqual(added_training.body, "Learning JavaScript fundamentals")
        self.assertEqual(added_training.status, "pending")
        # Update the training status
        updated_training = self.data_manager.update_training_status(
            added_training.user_id, added_skill.id, "completed"
        )
        # Check that the user's trainings list was updated
        self.assertIsNotNone(updated_training)
        self.assertEqual(updated_training.status, "completed")
