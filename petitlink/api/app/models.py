from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base


SQLALCHEMY_DATABASE_URL = 'sqlite:///app.db'

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)


class PetitLink(Base):
    __tablename__ = 'petit_link'

    id = Column(Integer, primary_key=True)
    original_link = Column(String)
    petit_link = Column(String)
    created_at = Column(DateTime)


init_db()
