import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend-service to Python path
sys.path.append("/backend-service")

from models.student import Student
from models.project_requirement import ProjectRequirement
from models.group import Group


# Path to SQLite DB inside /data
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "groupformation.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

from sqlalchemy.orm import declarative_base
Base = declarative_base()

# Bind models to Base metadata
Student.__table__.create(bind=engine, checkfirst=True)
ProjectRequirement.__table__.create(bind=engine, checkfirst=True)
Group.__table__.create(bind=engine, checkfirst=True)

print("Database initialized at:", DB_PATH)
