from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    # connect_args={'check_same_thread': False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)

class Base(DeclarativeBase):
    pass

def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@contextmanager
def get_or_create_session(session: Session | None = None):
    if session is None:
        with next(get_db()) as sess:
            yield sess
    else:
        yield session

db_context = contextmanager(get_db)
