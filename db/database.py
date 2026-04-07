import urllib.parse
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

# --- CONFIGURATION LOADING ---
app_env = settings.APP_ENV
env_file = f".env.{app_env}"
env_path = Path(__file__).resolve().parent.parent / "core" / env_file
load_dotenv(dotenv_path=env_path)
db_user = settings.DB_USER
raw_password: str = settings.DB_PASSWORD
db_host = settings.DB_HOST
db_port = settings.DB_PORT
db_name = settings.DB_NAME

encoded_password = urllib.parse.quote_plus(raw_password)

# --- DATABASE URLS ---
SQLALCHEMY_DATABASE_URL = (
    f"mysql+aiomysql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
)

# --- ENGINES ---
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,
    connect_args={
        "ssl": False
    },  # Disable SSL for local development; adjust as needed for production
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
