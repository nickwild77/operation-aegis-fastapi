"""SQLite initialization and parameterized queries."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL
)
"""

SEED_USERS = (
    ("alice", "customer"),
    ("bob", "analyst"),
)


def initialize_database(database_path: Path) -> None:
    """Create schema and deterministic demonstration data."""
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute(SCHEMA)

        connection.executemany(
            """
            INSERT OR IGNORE INTO users (username, role)
            VALUES (?, ?)
            """,
            SEED_USERS,
        )

        connection.commit()


def find_user_by_username(
    connection: sqlite3.Connection,
    username: str,
) -> sqlite3.Row | None:
    """Find a user with a parameterized SQL statement."""
    cursor = connection.execute(
        """
        SELECT id, username, role
        FROM users
        WHERE username = ?
        """,
        (username,),
    )

    return cursor.fetchone()
