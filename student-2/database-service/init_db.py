import os
import sqlite3

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
DATABASE_NAME = os.path.join(DATA_DIR, "skill_exchange.db")
os.makedirs(DATA_DIR, exist_ok=True)

conn = sqlite3.connect(DATABASE_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS skill_exchange_listings (
    listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    student_name TEXT NOT NULL,
    skill_offered TEXT NOT NULL,
    skill_wanted TEXT NOT NULL,
    availability TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
""")

existing = cursor.execute("SELECT COUNT(*) FROM skill_exchange_listings").fetchone()[0]
if existing == 0:
    rows = [
        (1001, "Alice Nguyen", "Python", "UI Design", "Tue Thu evenings", "Can help with Python fundamentals and Flask.", "active"),
        (1002, "Ben Carter", "UI Design", "Python", "Tue evenings Sat morning", "Can help with Figma, layout and accessibility.", "active"),
        (1003, "Chloe Martin", "Java", "Referencing", "Mon Wed afternoon", "Can help with Java OOP and debugging.", "active"),
        (1004, "Daniel Kim", "Referencing", "Java", "Wed afternoon Fri morning", "Can help with APA/IEEE referencing and source checks.", "active"),
        (1005, "Eva Singh", "Research", "SQL", "Mon Thu evening", "Can help with literature searches and research summaries.", "active"),
        (1006, "Farah Ali", "SQL", "Research", "Thu evening Sat afternoon", "Can help with SELECT, JOIN and SQLite queries.", "active"),
        (1007, "George Wilson", "Git", "Presentation", "Tue Fri afternoon", "Can help with Git branching, commits and pull requests.", "active"),
        (1008, "Hannah Lee", "Presentation", "Git", "Fri afternoon Sun evening", "Can help structure and rehearse technical presentations.", "active"),
        (1009, "Isaac Brown", "Diagramming", "C++", "Mon Wed evening", "Can help with ERDs, UML and architecture diagrams.", "active"),
        (1010, "Julia Chen", "C++", "Diagramming", "Wed evening Sat morning", "Can help with C++ syntax, classes and debugging.", "active"),
    ]
    cursor.executemany("""
        INSERT INTO skill_exchange_listings (
            student_id, student_name, skill_offered, skill_wanted,
            availability, description, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)

conn.commit()
count = cursor.execute("SELECT COUNT(*) FROM skill_exchange_listings").fetchone()[0]
conn.close()
print(f"Skill Exchange database ready with {count} listing(s).")
