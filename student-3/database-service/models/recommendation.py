from sqlalchemy import Column, Integer, String, JSON
from services.database_api import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True)
    subject = Column(String, nullable=False)
    recommendation = Column(JSON, nullable=False)
