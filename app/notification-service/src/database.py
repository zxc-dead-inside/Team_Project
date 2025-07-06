import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base


database_url = os.getenv(
    "DATABASE_URL",
    "postgresql://notification_user:notification_pass@localhost:5432/notification_db",
)

engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db

    except Exception:
        pass
    
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
