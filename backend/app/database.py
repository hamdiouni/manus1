"""
Database configuration and session management for the SLA Violation Prediction platform.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - defaults to PostgreSQL for production, SQLite for development
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@localhost:5432/sla_prediction"
)

# For development, use SQLite if PostgreSQL is not available
if DATABASE_URL.startswith("postgresql://"):
    try:
        engine = create_engine(DATABASE_URL)
        # Test connection
        engine.connect()
    except Exception:
        print("PostgreSQL not available, falling back to SQLite")
        DATABASE_URL = "sqlite:///./sla_prediction.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

