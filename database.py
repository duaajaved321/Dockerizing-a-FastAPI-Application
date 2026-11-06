"""SQLite persistence functions for patient vital records."""

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "patient_vitals.db"


def get_connection() -> sqlite3.Connection:
    """Open the database configured by DB_PATH, or use the project-local file."""
    db_path = os.getenv("DB_PATH", str(DEFAULT_DB_PATH))
    Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path, timeout=10)


def create_table() -> None:
    """Create the vitals table if it does not already exist."""
    with closing(get_connection()) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS vitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                age INTEGER NOT NULL,
                systolic INTEGER NOT NULL,
                diastolic INTEGER NOT NULL,
                glucose_level REAL NOT NULL
            )
            """
        )
        connection.commit()


def save_vitals(vitals: Any) -> None:
    """Insert a validated vital-sign record using parameterized SQL."""
    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO vitals (
                patient_id, age, systolic, diastolic, glucose_level
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                vitals.patient_id,
                vitals.age,
                vitals.blood_pressure.systolic,
                vitals.blood_pressure.diastolic,
                vitals.glucose_level,
            ),
        )
        connection.commit()


def get_patient_vitals(patient_id: str) -> list[dict[str, Any]]:
    """Return all records for one patient, newest first."""
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM vitals WHERE patient_id = ? ORDER BY id DESC",
            (patient_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_patient_summary(patient_id: str) -> dict[str, Any]:
    """Calculate average measurements and record count for one patient."""
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT
                AVG(systolic) AS avg_systolic,
                AVG(diastolic) AS avg_diastolic,
                AVG(glucose_level) AS avg_glucose,
                COUNT(*) AS total_records
            FROM vitals
            WHERE patient_id = ?
            """,
            (patient_id,),
        ).fetchone()
        return dict(row)
