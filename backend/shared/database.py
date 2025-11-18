import os
import inspect
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

backend_root = Path(__file__).parent.parent
load_dotenv(backend_root / ".env")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

SERVICE_DB_MAP = {
    "auth-service": os.getenv("CREDENTIAL_DB_NAME"),
    "device-service": os.getenv("DEVICE_DB_NAME"),
    "user-service": os.getenv("USER_DB_NAME"),
}


def _detect_service_name() -> str:
    frame = inspect.currentframe()
    try:
        while frame:
            frame_info = inspect.getframeinfo(frame)
            file_path = Path(frame_info.filename)
            
            for service_name in SERVICE_DB_MAP.keys():
                if service_name in file_path.parts:
                    return service_name
            
            frame = frame.f_back
    finally:
        del frame
    
    raise RuntimeError(
        "Could not detect microservice name. "
        "This module should be imported from auth-service, device-service, or user-service."
    )


def _get_database_url() -> str:
    service_name = _detect_service_name()
    db_name = SERVICE_DB_MAP.get(service_name)
    
    if not db_name:
        raise RuntimeError(
            f"No database configured for service '{service_name}'. "
            f"Check .env file for {service_name.upper().replace('-', '_')}_DB_NAME"
        )
    
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"

DATABASE_URL = _get_database_url()
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
