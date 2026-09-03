from sqlalchemy import Column, Integer, String, JSON
from services.database_api import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    skills = Column(JSON, nullable=True)  # Store skills as a JSON array
    