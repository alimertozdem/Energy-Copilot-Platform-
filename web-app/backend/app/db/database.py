"""Database engine and session configuration."""
import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

_raw_url = os.getenv("DATABASE_URL")
if not _raw_url:
    raise RuntimeError("DATABASE_URL is not set in .env")

# Supabase 'postgresql://' veriyor, biz psycopg3 kullanıyoruz.
# SQLAlchemy default 'postgresql://' --> psycopg2 arar (yok). Prefix'i duzelt.
if _raw_url.startswith("postgresql://"):
    DATABASE_URL = _raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    DATABASE_URL = _raw_url

# Supabase Session Pooler kullaniyoruz (IPv4 uyumlu).
# pool_pre_ping: pooler timeout sonrasi baglanti kopuksa otomatik yeniden baglan.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,  # True --> tum SQL'ler log'a basilir (debug icin)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Tum ORM modelleri bu siniftan miras alir."""
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: request basina bir session ac, sonunda kapat."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
