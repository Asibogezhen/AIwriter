"""数据库连接管理"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database

from app.config import settings

# SQLite 外键支持
engine = create_engine(
    settings.database_url_sync,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
    connect_args={"check_same_thread": False} if settings.db_type == "sqlite" else {},
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.db_type == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

database = Database(settings.database_url)


async def get_db():
    yield database
