from sqlalchemy import Column, Integer, String, JSON
from services.database_api import Base

class ProjectRequirement(Base):
    __tablename__ = "project_requirements"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, nullable=False)
    requirements = Column(JSON, nullable=True)  # Store required skills as a JSON array
