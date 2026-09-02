import sqlite3
import os


DATABASE = os.getenv(
    "DATABASE_PATH",
    "/app/data/project_management.db"
)


def initialise_database():

    # Make sure the directory exists.
    database_directory = os.path.dirname(DATABASE)

    if database_directory:
        os.makedirs(
            database_directory,
            exist_ok=True
        )

    connection = sqlite3.connect(DATABASE)

    # Enable foreign keys.
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    # -----------------------------------------------------
    # Projects
    # -----------------------------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            description TEXT,

            requirements TEXT,

            owner_id INTEGER NOT NULL,

            start_date TEXT,

            deadline TEXT,

            status TEXT NOT NULL DEFAULT 'Not Started'
        )
        """
    )

    # -----------------------------------------------------
    # Tasks
    # -----------------------------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            project_id INTEGER NOT NULL,

            title TEXT NOT NULL,

            description TEXT,

            assigned_student_id INTEGER,

            priority TEXT DEFAULT 'Medium',

            status TEXT NOT NULL DEFAULT 'Not Started',

            deadline TEXT,

            completion_date TEXT,

            FOREIGN KEY (project_id)
                REFERENCES projects(id)
                ON DELETE CASCADE
        )
        """
    )

    # -----------------------------------------------------
    # Milestones
    # -----------------------------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS milestones (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            project_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            description TEXT,

            deadline TEXT,

            completion_status INTEGER NOT NULL DEFAULT 0,

            FOREIGN KEY (project_id)
                REFERENCES projects(id)
                ON DELETE CASCADE
        )
        """
    )

    connection.commit()
    connection.close()

    print("Database initialised successfully.")
    print(f"Database location: {DATABASE}")


if __name__ == "__main__":
    initialise_database()