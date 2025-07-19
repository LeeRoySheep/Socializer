import datetime
from os import path
from typing import Optional, Generator

from sqlmodel import Field, Session, SQLModel, create_engine

# Define Base for SQLAlchemy ORM
Base = SQLModel


class User(Base, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    role: str = Field(default="user")
    hashed_name: str = Field(default=None)
    hashed_password: str = Field(default=None)
    hashed_email: str = Field(default=None)
    member_since: datetime.date = Field(default=datetime.datetime.now().date())

    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, role={self.role})"

    def __str__(self):
        return f"User {self.username} (ID: {self.id})"


class Skill(Base, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    skill_name: str = Field(default=None, unique=True)


    def __repr__(self):
        return f"Skill(id={self.id}, name={self.skill_name}, level={self.level})"

    def __str__(self):
        return f"Skill {self.skill_name} (Level: {self.level})"


class UserSkill(Base, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    skill_id: Optional[int] = Field(default=None, foreign_key="skill.id", primary_key=True)
    level: int = Field(default=0)


class Training(SQLModel, table=True):
    user_id: int = Field(default=None, foreign_key="user.id", primary_key=True)
    skill_id: int = Field(default=None, foreign_key="skill.id", primary_key=True)
    body: str = Field(default=None)
    status: str = Field(default=None)
    absolved: bool = Field(default=False)
    started_at: datetime.date = Field(default=None)

    def __repr__(self):
        return f"Training(user_id={self.user_id}, skill_id={self.skill_id}, status={self.status})"

    def __str__(self):
        return f"Training for User {self.user_id} on Skill {self.skill_id}"


class DataModel:
    sqlite_file_name = "users_datas.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"

    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, connect_args=connect_args)

    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        with Session(self.engine) as session:
            yield session


if __name__ == "__main__":
    data = DataModel()
    print(f"Initializing database at {DataModel.sqlite_url}...")
    if path.exists(DataModel.sqlite_url):
        print("Database already exists, skipping...")
    else:
        data.create_db_and_tables()
        print("Database created.")
