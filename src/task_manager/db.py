"""Database configuration module for standalone task application."""

import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base class for all models
Base = declarative_base()

class DatabaseConfig:
    """Database configuration and session management."""
    
    def __init__(self, dsn: Optional[str] = None):
        """Initialize database configuration.
        
        Args:
            dsn: Database connection string. If None, will read from environment.
        """
        self.dsn = dsn or self._get_dsn_from_env()
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _get_dsn_from_env(self) -> str:
        """Get database DSN from environment variables."""
        # Try different environment variable names
        dsn_vars = ['DATABASE_URL', 'DATABASE_DSN', 'DB_URL', 'DB_DSN']
        
        for var in dsn_vars:
            dsn = os.getenv(var)
            if dsn:
                return dsn
        
        # Fallback: construct DSN from individual components
        db_type = os.getenv('DB_TYPE', 'postgresql')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'tasks_db')
        
        if db_type.lower() == 'sqlite':
            return f"sqlite:///{db_name}.db"
        elif db_type.lower() == 'mysql':
            return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:  # PostgreSQL
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    def _initialize_database(self):
        """Initialize database engine and session factory."""
        self.engine = create_engine(
            self.dsn,
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    def get_engine(self):
        """Get the database engine."""
        return self.engine

# Global database instance
_db_instance = None

def get_db() -> DatabaseConfig:
    """Get the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConfig()
    return _db_instance

def get_session() -> Session:
    """Get a new database session."""
    return get_db().get_session()

def init_db(dsn: Optional[str] = None):
    """Initialize the database with optional custom DSN."""
    global _db_instance
    _db_instance = DatabaseConfig(dsn)
    _db_instance.create_tables()
    return _db_instance

# Context manager for database sessions
class DatabaseSession:
    """Context manager for database sessions."""
    
    def __init__(self):
        self.session = None
    
    def __enter__(self) -> Session:
        self.session = get_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()