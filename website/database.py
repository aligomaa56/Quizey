""" This file is used to create a database connection and session for the FastAPI application. """
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings


SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """ Create a new database session.
    Returns:
        Session: A new database session.
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
