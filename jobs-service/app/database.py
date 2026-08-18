import os
from pathlib import Path
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    password_file = os.getenv(
        "POSTGRES_PASSWORD_FILE",
        "/run/secrets/db_password",
    )


    password = Path(password_file).read_text().strip()

    encoded_password = quote_plus(password)

    DATABASE_URL = (
        f"postgresql://"
        f"{os.getenv('POSTGRES_USER', 'postgres')}:"
        f"{encoded_password}@"
        f"{os.getenv('POSTGRES_HOST', 'postgres')}:5432/"
        f"{os.getenv('POSTGRES_DB', 'jobboard')}"
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
