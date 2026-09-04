from sqlalchemy import Column, Integer, String, JSON
from services.database_api import Base
from sqlalchemy.ext.mutable import MutableDict

class ProjectRequirement(Base):
    __tablename__ = "project_requirements"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, nullable=False)
    requirements = Column(MutableDict.as_mutable(JSON), nullable=False)  # Store required skills as a JSON array
