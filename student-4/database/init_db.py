import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "skill_profile.db")


def init_db():

    os.makedirs(DATA_DIR, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")


    # CREATE SKILL PROFILES TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_profiles (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # CREATE STUDENT SKILLS TABLE
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


    # SEED DATA
    seed_profiles = [
        {
            "student_id": 1,
            "skills": [
                ("Python", "Intermediate", "Problem solving", "Advanced libraries"),
                ("SQL", "Intermediate", "Database queries", "Query optimisation")
            ]
        },
        {
            "student_id": 2,
            "skills": [
                ("JavaScript", "Advanced", "Frontend development", "Testing"),
                ("HTML/CSS", "Advanced", "Responsive design", "Accessibility")
            ]
        },
        {
            "student_id": 3,
            "skills": [
                ("Java", "Intermediate", "Object-oriented programming", "Concurrency"),
                ("Git", "Intermediate", "Version control", "Merge conflicts")
            ]
        },
        {
            "student_id": 4,
            "skills": [
                ("Python", "Intermediate", "Problem solving", "Advanced libraries"),
                ("Flask", "Beginner", "API development", "Application structure")
            ]
        },
        {
            "student_id": 5,
            "skills": [
                ("C#", "Intermediate", "Application logic", "Async programming"),
                ("SQL", "Beginner", "Basic queries", "Database design")
            ]
        },
        {
            "student_id": 6,
            "skills": [
                ("React", "Intermediate", "UI components", "State management"),
                ("JavaScript", "Intermediate", "Web development", "Advanced patterns")
            ]
        },
        {
            "student_id": 7,
            "skills": [
                ("Docker", "Beginner", "Container basics", "Networking"),
                ("GitHub Actions", "Beginner", "Basic workflows", "Advanced CI/CD")
            ]
        },
        {
            "student_id": 8,
            "skills": [
                ("Python", "Advanced", "Automation", "Machine learning"),
                ("Flask", "Intermediate", "REST APIs", "Production deployment")
            ]
        },
        {
            "student_id": 9,
            "skills": [
                ("UI/UX Design", "Intermediate", "Wireframing", "User testing"),
                ("Figma", "Advanced", "Prototyping", "Design systems")
            ]
        },
        {
            "student_id": 10,
            "skills": [
                ("Project Management", "Intermediate", "Team coordination", "Risk planning"),
                ("Agile", "Intermediate", "Sprint planning", "Estimation")
            ]
        }
    ]


    for profile in seed_profiles:

        student_id = profile["student_id"]

        # Check whether this student already has a profile
        existing_profile = cursor.execute("""
            SELECT profile_id
            FROM skill_profiles
            WHERE student_id = ?
            LIMIT 1
        """, (student_id,)).fetchone()


        # Only seed if the student does not already exist
        if existing_profile is None:

            cursor.execute("""
                INSERT INTO skill_profiles (student_id)
                VALUES (?)
            """, (student_id,))

            profile_id = cursor.lastrowid


            for skill in profile["skills"]:

                cursor.execute("""
                    INSERT INTO student_skills (
                        profile_id,
                        skill_name,
                        skill_level,
                        strength,
                        weakness
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    profile_id,
                    skill[0],
                    skill[1],
                    skill[2],
                    skill[3]
                ))


    connection.commit()
    connection.close()

    print("Skill Profile database created and seeded successfully.")


if __name__ == "__main__":
    init_db()