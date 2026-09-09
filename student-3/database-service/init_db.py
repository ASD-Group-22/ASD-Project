import sys
sys.path.append("/backend-service")

from services.database_api import Base, engine, SessionLocal
from models.subject import Subject

Base.metadata.create_all(bind=engine)

session = SessionLocal()

default_subjects = ["ASD", "CCI", "AI", "CITP", "Cryptography"]

for name in default_subjects:
    if not session.query(Subject).filter_by(name=name).first():
        session.add(Subject(name=name))

session.commit()
session.close()

print("Database initialized with default subjects at /app/data/groupformation.db.")