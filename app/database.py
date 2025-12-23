"""
╔════════════════════════════════════════════════════════════════════════════╗
║         DATABASE CONFIGURATION - THE CONNECTION LAYER                      ║
║                                                                            ║
║  SQLAlchemy setup for connecting to PostgreSQL database.                  ║
║  This is where the "magic" of ORM happens.                                ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ────────────────────────────────────────────────────────────────────────────
# DATABASE URL
# ────────────────────────────────────────────────────────────────────────────
# Format: postgresql://username:password@localhost:5432/database_name
# 
# This tells SQLAlchemy WHERE to connect.
# Currently uses SQLite (simple, no setup needed).
# For production, change to PostgreSQL or MySQL.

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./test.db"  # Default: SQLite file in project root
)

# ────────────────────────────────────────────────────────────────────────────
# CREATE ENGINE
# ────────────────────────────────────────────────────────────────────────────
# The Engine is SQLAlchemy's connection to the database.
# Think of it as a "factory" that creates connections when needed.

# Configure connection arguments based on database type
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}  # SQLite specific

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

# ────────────────────────────────────────────────────────────────────────────
# SESSION FACTORY
# ────────────────────────────────────────────────────────────────────────────
# A "session" is a conversation with the database.
# SessionLocal is a factory that creates new sessions.
# 
# Each HTTP request gets its own session.
# When request ends, session closes.

SessionLocal = sessionmaker(
    autocommit=False,  # Don't auto-commit (we control when to save)
    autoflush=False,   # Don't auto-flush (we control when to sync)
    bind=engine        # Use the engine above
)

# ────────────────────────────────────────────────────────────────────────────
# DECLARATIVE BASE
# ────────────────────────────────────────────────────────────────────────────
# This is the parent class for all ORM models.
# Every database table must inherit from Base.
# 
# When we later do: Base.metadata.create_all(bind=engine)
# SQLAlchemy looks at all classes inheriting from Base
# and creates corresponding tables in the database.

Base = declarative_base()


# ────────────────────────────────────────────────────────────────────────────
# DEPENDENCY FUNCTION: get_db()
# ────────────────────────────────────────────────────────────────────────────
# This is FastAPI's "dependency injection" pattern.
# 
# Usage in an endpoint:
#   def my_endpoint(db: Session = Depends(get_db)):
#       db.query(...)  # Use the database session
# 
# FastAPI automatically:
#   1. Calls get_db()
#   2. Passes the session to your endpoint
#   3. Closes the session when endpoint finishes

def get_db():
    """
    Dependency function that provides a database session.
    
    This is a "generator" function (yields instead of returns).
    
    Lifecycle:
    1. FastAPI calls this function
    2. It creates a session (yield)
    3. Endpoint uses the session
    4. Endpoint finishes
    5. Finally block closes the session
    
    Why? Ensures database connections are properly managed.
    """
    db = SessionLocal()
    try:
        yield db  # Give the session to the endpoint
    finally:
        db.close()  # Always close the connection when done
