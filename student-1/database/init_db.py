import os
import sqlite3


DATABASE_PATH = "/app/data/project_management.db"


def initialise_database():

    os.makedirs(
        os.path.dirname(DATABASE_PATH),
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    # -----------------------------------------------------
    # PROJECTS TABLE
    # -----------------------------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT NOT NULL DEFAULT 'Not Started'
        )
        """
    )

    # -----------------------------------------------------
    # TASKS TABLE
    # -----------------------------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',

            FOREIGN KEY (project_id)
                REFERENCES projects(id)
                ON DELETE CASCADE
        )
        """
    )

    # -----------------------------------------------------
    # SAMPLE DATA
    # -----------------------------------------------------

    project_count = connection.execute(
        "SELECT COUNT(*) FROM projects"
    ).fetchone()[0]

    if project_count == 0:

        projects = [
            (
                "Student Management System",
                "A web application for managing student information and enrolments.",
                "2026-09-01",
                "2026-11-30",
                "In Progress"
            ),
            (
                "E-Commerce Platform",
                "An online shopping platform for customers to browse and purchase products.",
                "2026-09-05",
                "2026-12-15",
                "In Progress"
            ),
            (
                "Mobile Fitness Application",
                "A mobile application for tracking workouts and fitness progress.",
                "2026-09-10",
                "2027-01-15",
                "Not Started"
            ),
            (
                "Library Management System",
                "A system for managing books, members and library loans.",
                "2026-09-15",
                "2026-12-01",
                "In Progress"
            ),
            (
                "Event Booking Platform",
                "A platform for users to discover and book events.",
                "2026-10-01",
                "2027-02-28",
                "Not Started"
            ),
            (
                "Project Management Application",
                "An application for managing projects, tasks and project progress.",
                "2026-09-01",
                "2027-01-31",
                "In Progress"
            ),
            (
                "Online Learning Platform",
                "A platform providing online courses and learning resources.",
                "2026-10-01",
                "2027-03-31",
                "Not Started"
            ),
            (
                "Restaurant Ordering System",
                "A web application allowing customers to order food online.",
                "2026-09-20",
                "2026-12-20",
                "Not Started"
            ),
            (
                "Healthcare Appointment System",
                "A system for managing patient appointments and schedules.",
                "2026-10-15",
                "2027-03-15",
                "Not Started"
            ),
            (
                "Community Social Platform",
                "A social platform for users to create posts and interact with communities.",
                "2026-11-01",
                "2027-04-30",
                "Not Started"
            )
        ]

        connection.executemany(
            """
            INSERT INTO projects (
                name,
                description,
                start_date,
                end_date,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            projects
        )

        # -------------------------------------------------
        # SAMPLE TASKS
        # -------------------------------------------------

        tasks = [
            (1, "Design the database schema", "Complete"),
            (1, "Implement student registration", "In Progress"),
            (1, "Create student dashboard", "Pending"),

            (2, "Design product catalogue", "Complete"),
            (2, "Implement shopping cart", "In Progress"),
            (2, "Implement checkout process", "Pending"),

            (3, "Design workout tracking interface", "Pending"),
            (3, "Implement workout tracking", "Pending"),

            (4, "Create book database", "Complete"),
            (4, "Implement book search", "In Progress"),

            (5, "Design event catalogue", "Pending"),
            (5, "Implement event booking", "Pending"),

            (6, "Create project database", "Complete"),
            (6, "Implement task management", "In Progress"),
            (6, "Implement AI task generation", "In Progress"),

            (7, "Create course catalogue", "Pending"),
            (7, "Implement course enrolment", "Pending"),

            (8, "Create restaurant menu", "Pending"),
            (8, "Implement online ordering", "Pending"),

            (9, "Design appointment database", "Pending"),
            (9, "Implement appointment booking", "Pending"),

            (10, "Design community feed", "Pending"),
            (10, "Implement user posts", "Pending")
        ]

        connection.executemany(
            """
            INSERT INTO tasks (
                project_id,
                task,
                status
            )
            VALUES (?, ?, ?)
            """,
            tasks
        )

        print(
            "Created 10 sample projects and sample tasks."
        )

    else:

        print(
            f"Database already contains "
            f"{project_count} projects. "
            "Sample data was not added."
        )

    connection.commit()
    connection.close()

    print(
        "Database initialised successfully."
    )


if __name__ == "__main__":
    initialise_database()