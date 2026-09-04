from sqlalchemy import Column, Integer, String, JSON
from services.database_api import Base

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    members = Column(JSON, nullable=True)  # Store member IDs as a JSON array