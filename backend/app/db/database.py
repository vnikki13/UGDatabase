from typing import Annotated
from fastapi import Depends
from sqlmodel import Session, create_engine, SQLModel
from app.core.config import settings


# The engine is the single object that we share with all the code.
# It's in charge of communicating with the database, handling the connections, ect.
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=True,  # See all SQL statements, remove in production
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
