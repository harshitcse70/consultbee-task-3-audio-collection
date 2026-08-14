import os
import sqlite3

# Path to the Task 1 SQLite database
DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "../consultbae-assignment/data/consultbae.db"
)


def get_db_connection():
    """Create and return a SQLite database connection."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection