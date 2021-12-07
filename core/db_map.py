from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import Column, BigInteger, String, create_engine, CheckConstraint, Boolean, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from config import DB_URL

Base = declarative_base()
engine = create_engine(DB_URL, echo=False, pool_size=8, max_overflow=12)

session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


@contextmanager
def session_scope():
    session = Session()

    try:
        yield session
        session.commit()

    except:
        session.rollback()
        raise

    finally:
        session.close()


class UsersTable(Base):
    __tablename__ = 'users_table'
    id = Column(BigInteger, primary_key=True, nullable=False)
    sub = Column(TIMESTAMP)
