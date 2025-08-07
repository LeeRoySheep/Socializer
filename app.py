import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import jwt
from dotenv import load_dotenv, find_dotenv
from fastapi import Depends, FastAPI, HTTPException, status, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel import Session, select

from datamanager.data_manager import DataManager
from datamanager.data_model import DataModel, User, Skill, Training

# Find and load the .env file
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "No SECRET_KEY environment variable set. Please set it in .env file."
    )
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Specify the templates directory
templates = Jinja2Templates(directory="templates")


# Models for API requests and responses
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    skills: List[int]
    trainings: List[int]


class SkillCreate(BaseModel):
    skill_name: str
    level: int = 0


class TrainingCreate(BaseModel):
    skill_id: int
    body: str
    status: str = "pending"


# Initialize FastAPI app
app = FastAPI(title="Skills Training API")

# Allow CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize data model and manager
data_model = DataModel()
data_manager = DataManager()


# Database dependency
def get_db():
    db = Session(data_model.engine)
    try:
        yield db
    finally:
        db.close()


# Helper functions for authentication
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db: Session, username: str):
    """Retrieve user by username from database"""
    # return db.query(User).filter(User.username == username).first()  # SQLAlchemy query
    # return db.get(User, username)  # SQLModel query
    # return data_model.get_user_by_username(username)  # SQLModel query

    return data_manager.get_user_by_username(username)


def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception

    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user


async def get_user_skills(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[int] | None:

    return DataManager.get_skills_for_user(current_user.id)


@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    """form for user registration"""
    return templates.TemplateResponse("register.html", {"request": request})


# Routes
@app.post("/register")
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = User(
        username=username,
        hashed_email=get_password_hash(email),
        hashed_password=get_password_hash(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User successfully registered"}


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """form for user registration"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    # In a stateless JWT system, the client simply discards the token
    # Server-side we don't need to do anything
    return {"message": "Successfully logged out"}


@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        skills=current_user.get_skills(),
        trainings=current_user.get_trainings(),
    )


@app.post("/skills")
async def add_skill(
    skill: SkillCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Create new skill linked to the current user
    new_skill = Skill(
        user_id=current_user.id, skill_name=skill.skill_name, level=skill.level
    )

    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)

    # Update user's skills list
    skills = current_user.get_skills()
    skills.append(new_skill.id)
    current_user.set_skills(skills)

    db.add(current_user)
    db.commit()

    return {"message": "Skill added successfully", "skill_id": new_skill.id}


@app.post("/training/start")
async def start_training(
    training: TrainingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Check if the skill exists
    skill_statement = select(Skill).where(Skill.id == training.skill_id)
    skill = db.exec(skill_statement).first()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found"
        )

    # Create new training
    new_training = Training(
        user_id=current_user.id,
        skill_id=training.skill_id,
        body=training.body,
        status=training.status,
        started_at=datetime.now().date(),
    )

    db.add(new_training)
    db.commit()

    # Update user's trainings list
    trainings = data_manager.get_training_for_user(current_user.id)
    trainings.append(new_training.skill_id)  # Using skill_id as identifier
    current_user.set_trainings(trainings)

    db.add(current_user)
    db.commit()

    return {"message": "Training started successfully"}


@app.put("/skills/{skill_id}/evaluate")
async def evaluate_skill(
    skill_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    level: int = Form(...),
):
    # Check if the user has the skill
    skill_statement = select(Skill).where(
        Skill.id == skill_id, Skill.user_id == current_user.id
    )
    skill = db.exec(skill_statement).first()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found or not owned by current user",
        )

    # Update skill level
    skill.level = level
    db.add(skill)
    db.commit()

    return {"message": "Skill evaluated successfully", "new_level": level}


@app.put("/training/{skill_id}/complete")
async def complete_training(
    skill_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Find the training
    training_statement = select(Training).where(
        Training.user_id == current_user.id, Training.skill_id == skill_id
    )
    training = db.exec(training_statement).first()

    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Training not found"
        )

    # Mark as completed
    training.status = "completed"
    training.absolved = True
    db.add(training)
    db.commit()

    return {"message": "Training completed successfully"}


# Startup event to ensure database is created
@app.on_event("startup")
def on_startup():
    data_model.create_db_and_tables()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
