from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ----------------------------------------------------------------------------------
# SQLITE CONFIGURATION
# This will automatically create a file named 'pharmacy.db' in your backend folder.
# No installation required!
# ----------------------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./pharmacy.db"

# connect_args={"check_same_thread": False} is required only for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to provide a database session to FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()