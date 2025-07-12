from os import path
from typing import Annotated
import datetime

from fastapi import Depends, FastAPI
from sqlmodel import Field, Session, SQLModel, create_engine, select

class DataModel:

    class User(SQLModel, table=True):
        id: int = Field(unique=True, primary_key=True)
        username: str = Field(unique=True)
        role: str = Field(default="user")
        skills: list[int] = Field(default=[])
        trainings: list[int] = Field(default=[])
        hashed_name: str = Field(default=None,)
        hashed_password: str = Field(default=None)
        hashed_email: str = Field(default=None)
        member_since: datetime.date = Field(default=datetime.datetime.now())

        def __repr__(self):
            return f"User(id={self.id}, username={self.username}, role={self.role})"

        def __str__(self):
            return f"User {self.username} (ID: {self.id})"


    class Skill(SQLModel, table=True):
        id: int = Field(unique=True, primary_key=True)
        user_id: int = Field(default=None, foreign_key="user.id")
        skill_name: str = Field(default=None, unique=True)
        level: int = Field(default=0)

        def __repr__(self):
            return f"Skill(id={self.id}, name={self.skill_name}, level={self.level})"

        def __str__(self):
            return f"Skill {self.skill_name} (Level: {self.level})"

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


    sqlite_file_name = "users_datas.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"

    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, connect_args=connect_args)

    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)


    def get_session(self):
        with Session(self.engine) as session:
            yield session
            yield session


    SessionDep = Annotated[Session, Depends(get_session)]

    app = FastAPI()










if __name__ == "__main__":
    data = DataModel()
    print(f"Initializing database at {DataModel.sqlite_url}...")
    if path.exists(DataModel.sqlite_url):
        print("Database already exists, skipping...")
    else:
        data.create_db_and_tables()
        print("Database created.")



