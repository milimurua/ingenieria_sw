from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import settings


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS bases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    priority INTEGER NOT NULL,
    min_staff INTEGER NOT NULL,
    required_vehicle TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS personnel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    home_base_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'available',
    is_driver INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(home_base_id) REFERENCES bases(id)
);

CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    vehicle_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'available',
    current_base_id INTEGER,
    FOREIGN KEY(current_base_id) REFERENCES bases(id)
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    vehicle_id INTEGER,
    assigned_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(base_id) REFERENCES bases(id),
    FOREIGN KEY(person_id) REFERENCES personnel(id),
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS absences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    reported_by TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    replacement_person_id INTEGER,
    FOREIGN KEY(person_id) REFERENCES personnel(id),
    FOREIGN KEY(replacement_person_id) REFERENCES personnel(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open'
);
"""


def ensure_database() -> None:
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


@contextmanager
def get_connection():
    ensure_database()
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
