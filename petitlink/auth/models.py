from __future__ import annotations

from typing import AsyncIterable

from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session


SQLALCHEMY_DATABASE_URL = 'sqlite:///auth.db'

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db() -> AsyncIterable[Session]:
    """Connect to database session and close connection after use"""
    db = session_factory()

    try:
        yield db
    finally:
        db.close()


class UserTable(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String)
    password_hash = Column(String)
    created_at = Column(DateTime)

    @classmethod
    def find_user_by_email(cls, db: Session, email: str):
        return db.query(UserTable).filter_by(email=email).first()


init_db()
