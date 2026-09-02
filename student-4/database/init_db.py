import sqlite3
import os


# Create path to database file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "skill_profile.db")


def init_db():

    # Make sure data folder exists
    os.makedirs(DATA_DIR, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    # Create skill_profiles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_profiles (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create student_skills table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_skills (
            student_skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            skill_name TEXT NOT NULL,
            skill_level TEXT NOT NULL,
            strength TEXT,
            weakness TEXT,
            FOREIGN KEY (profile_id)
                REFERENCES skill_profiles(profile_id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()

    print("Skill Profile database created successfully.")


if __name__ == "__main__":
    init_db()