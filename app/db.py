from __future__ import annotations

import mysql.connector
from contextlib import contextmanager

from app.config import settings


SCHEMA_SQL = """

CREATE TABLE IF NOT EXISTS bases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    priority INT NOT NULL,
    min_staff INT NOT NULL,
    required_vehicle VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS personnel (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(100) NOT NULL,
    home_base_id INT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'available',
    is_driver BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY(home_base_id) REFERENCES bases(id)
);

CREATE TABLE IF NOT EXISTS vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    vehicle_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'available',
    current_base_id INT,
    FOREIGN KEY(current_base_id) REFERENCES bases(id)
);

CREATE TABLE IF NOT EXISTS assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    base_id INT NOT NULL,
    person_id INT NOT NULL,
    vehicle_id INT,
    assigned_at DATETIME NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY(base_id) REFERENCES bases(id),
    FOREIGN KEY(person_id) REFERENCES personnel(id),
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS absences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL,
    reason TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    reported_by VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    replacement_person_id INT,
    FOREIGN KEY(person_id) REFERENCES personnel(id),
    FOREIGN KEY(replacement_person_id) REFERENCES personnel(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(255),
    created_at DATETIME NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'open'
);
"""


def create_database_if_not_exists():

    conn = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password
    )

    cursor = conn.cursor()

    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS {settings.mysql_database}"
    )

    conn.commit()

    cursor.close()
    conn.close()


def ensure_database() -> None:

    create_database_if_not_exists()

    conn = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database
    )

    cursor = conn.cursor()

    for statement in SCHEMA_SQL.split(";"):

        stmt = statement.strip()

        if stmt:
            cursor.execute(stmt)

    conn.commit()

    cursor.close()
    conn.close()


@contextmanager
def get_connection():

    ensure_database()

    conn = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database
    )

    cursor = conn.cursor(dictionary=True)

    try:
        yield cursor
        conn.commit()

    finally:
        cursor.close()
        conn.close()