import sys
import os

# Add backend-service to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend-service")))

from services.database_api import SessionLocal
from models.student import Student
from models.project_requirement import ProjectRequirement


db = SessionLocal()

students = [
    Student(name="Alice", email="alice@example.com", skills={"python": "expert", "teamwork": "intermediate"}),
    Student(name="Bob", email="bob@example.com", skills={"java": "intermediate", "leadership": "advanced"}),
    Student(name="Charlie", email="charlie@example.com", skills={"python": "beginner", "design": "intermediate"})
]

requirements = ProjectRequirement(
    subject="Software Engineering Project",
    requirements={
        "python": {"level": "intermediate", "amount": "extensive"},
        "teamwork": {"level": "intermediate", "amount": "moderate"},
        "design": {"level": "intermediate", "amount": "moderate"}
    }
)

db.add_all(students)
db.add(requirements)
db.commit()

print("Database seeded successfully.")
