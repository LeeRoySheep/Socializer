import os
from datetime import datetime, timedelta
from typing import Generator

import pytest
from dotenv import load_dotenv, find_dotenv
from fastapi.testclient import TestClient
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Load test environment variables
dotenv_path = find_dotenv('.env.test')
load_dotenv(dotenv_path)

# Import the app after environment is set
from app.main import app, get_db
from datamanager.data_model import Base, User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Test database URL - using in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine and session factory
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Test user data
TEST_USER_USERNAME = "testuser"
TEST_USER_PASSWORD = "testpassword"
TEST_USER_EMAIL = "test@example.com"

# Create a test database session for each test case
@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for testing.
    
    The session is automatically rolled back after each test.
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    # Start a nested transaction (using SAVEPOINT).
    nested = connection.begin_nested()
    
    # If the application code calls session.commit, it will end the nested
    # transaction. We need to start a new one when that happens.
    @event.listens_for(session, 'after_transaction_end')
    def restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active and connection.in_transaction():
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client that uses the override_get_db fixture."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    """Create a test user in the database."""
    from datamanager.data_model import User
    
    # Create test user with all required fields
    user = User(
        username=TEST_USER_USERNAME,
        hashed_password=pwd_context.hash(TEST_USER_PASSWORD),
        hashed_email=TEST_USER_EMAIL,
        role="user",
        temperature=0.7,
        preferences={},
        member_since=datetime.date.today(),
        messages=0
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user

@pytest.fixture
def auth_token(test_user):
    """Generate an access token for the test user."""
    from datetime import datetime, timedelta
    from jose import jwt
    
    access_token_expires = timedelta(minutes=30)
    expire = datetime.utcnow() + access_token_expires
    
    to_encode = {
        "sub": test_user.username,
        "exp": expire,
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        os.getenv("SECRET_KEY"), 
        algorithm=os.getenv("ALGORITHM")
    )
    
    return encoded_jwt
    """Create a test user in the database."""
    # Delete any existing test users
    db_session.query(User).filter(User.username == TEST_USER_USERNAME).delete()
    db_session.commit()
    
    # Hash the password
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(TEST_USER_PASSWORD)
    
    # Create test user
    user = User(
        username=TEST_USER_USERNAME,
        email=TEST_USER_EMAIL,
        hashed_password=hashed_password,
        is_active=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return {
        "username": user.username,
        "email": user.email,
        "password": TEST_USER_PASSWORD,
        "id": user.id
    }

# Authentication token fixture
@pytest.fixture
def auth_token(test_user) -> str:
    """Generate an access token for the test user."""
    # Create token data
    access_token_expires = timedelta(minutes=30)
    to_encode = {
        "sub": test_user.username,
        "exp": datetime.utcnow() + access_token_expires
    }
    
    # Create token
    secret_key = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM", "HS256")
    token = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    
    return token

# Dependency override for the database session
@pytest.fixture
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override the app's dependency
app.dependency_overrides[get_db] = override_get_db

# Test client with overridden dependencies
@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    with TestClient(app) as client:
        yield client
@pytest.fixture(scope="function")
def test_session() -> Generator[Session, None, None]:
    """Create a test database session with a savepoint, and roll back after the test.
    
    This ensures each test runs in its own transaction.
    """
    # Create tables if they don't exist
    Base.metadata.create_all(bind=test_engine)
    
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Begin a nested transaction (using SAVEPOINT).
    nested = connection.begin_nested()
    
    # If the application code calls session.commit, it will end the nested
    # transaction. We need to start a new one when that happens.
    @event.listens_for(session, 'after_transaction_end')
    def restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active and connection.in_transaction():
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        # Cleanup
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def test_client(test_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application with test database session."""
    def override_get_db():
        try:
            yield test_session
        finally:
            pass
    
    # Override the get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client with the overridden dependencies
    with TestClient(app) as client:
        yield client
    
    # Clear overrides after the test
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(test_session: Session) -> User:
    """Create a test user in the database."""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash("testpassword")
    
    # Clean up any existing test user
    test_session.query(User).filter(User.username == "testuser").delete()
    test_session.commit()
    
    # Create a new test user
    user = User(
        username="testuser",
        hashed_email="test@example.com",
        hashed_password=hashed_password,
        role="user",
        member_since=datetime.now()
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user
