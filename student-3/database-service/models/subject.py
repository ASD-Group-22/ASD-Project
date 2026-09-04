from sqlalchemy import Column, Integer, String
from services.database_api import Base

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
