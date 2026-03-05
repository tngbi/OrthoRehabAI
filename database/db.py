"""
SQLite database layer for OrthoRehabAI.
Handles all database creation, connection, and CRUD operations.
"""

import sqlite3
import os
from typing import Optional
from contextlib import contextmanager

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "orthorehab.db")


def _ensure_dir() -> None:
    os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_connection():
    """Yields a SQLite connection with WAL mode and foreign keys enabled."""
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they don't exist."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL,
                age          INTEGER,
                gender       TEXT,
                height_cm    REAL,
                weight_kg    REAL,
                surgery_date TEXT NOT NULL,
                surgeon      TEXT,
                injury_type  TEXT DEFAULT 'Achilles Tendon Repair',
                comorbidities TEXT,
                notes        TEXT,
                created_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS assessments (
                assessment_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id          INTEGER NOT NULL,
                assessment_date     TEXT NOT NULL DEFAULT (date('now')),
                weeks_post_op       REAL,
                phase               TEXT,

                -- ROM
                df_operative        REAL,
                df_non_operative    REAL,
                pf_operative        REAL,
                pf_non_operative    REAL,

                -- Pain & swelling
                pain_score          REAL,
                swelling_present    INTEGER DEFAULT 0,

                -- Functional tests
                heel_rise_operative       INTEGER,
                heel_rise_non_operative   INTEGER,
                single_hop_operative      REAL,
                single_hop_non_operative  REAL,
                triple_hop_operative      REAL,
                triple_hop_non_operative  REAL,
                crossover_hop_operative   REAL,
                crossover_hop_non_operative REAL,
                vertical_jump_operative   REAL,
                vertical_jump_non_operative REAL,

                -- Y-balance
                y_balance_anterior_op     REAL,
                y_balance_anterior_non    REAL,
                y_balance_pm_op           REAL,
                y_balance_pm_non          REAL,
                y_balance_pl_op           REAL,
                y_balance_pl_non          REAL,

                -- Strength
                leg_press_1rm_operative     REAL,
                leg_press_1rm_non_operative REAL,

                -- Psych readiness
                psych_readiness        REAL,

                -- Computed LSIs
                lsi_heel_rise          REAL,
                lsi_single_hop         REAL,
                lsi_triple_hop         REAL,
                lsi_crossover_hop      REAL,
                lsi_vertical_jump      REAL,
                lsi_y_balance          REAL,
                lsi_leg_press          REAL,

                -- Clinician notes
                clinician_notes        TEXT,

                FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS alerts (
                alert_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id     INTEGER NOT NULL,
                assessment_id  INTEGER,
                alert_date     TEXT DEFAULT (datetime('now')),
                severity       TEXT DEFAULT 'warning',
                message        TEXT NOT NULL,
                resolved       INTEGER DEFAULT 0,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
                FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id) ON DELETE SET NULL
            );
        """)


# ---------------------------------------------------------------------------
# Patient CRUD
# ---------------------------------------------------------------------------

def create_patient(name: str, surgery_date: str, age: Optional[int] = None,
                   gender: Optional[str] = None, height_cm: Optional[float] = None,
                   weight_kg: Optional[float] = None, surgeon: Optional[str] = None,
                   injury_type: str = "Achilles Tendon Repair",
                   comorbidities: Optional[str] = None,
                   notes: Optional[str] = None) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO patients
               (name, age, gender, height_cm, weight_kg, surgery_date, surgeon,
                injury_type, comorbidities, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, age, gender, height_cm, weight_kg, surgery_date, surgeon,
             injury_type, comorbidities, notes)
        )
        return cur.lastrowid


def update_patient(patient_id: int, **kwargs) -> None:
    allowed = {"name", "age", "gender", "height_cm", "weight_kg", "surgery_date",
               "surgeon", "injury_type", "comorbidities", "notes"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [patient_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE patients SET {set_clause} WHERE patient_id = ?", values)


def delete_patient(patient_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))


def list_patients() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM patients ORDER BY name").fetchall()
        return [dict(r) for r in rows]


def load_patient(patient_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM patients WHERE patient_id = ?",
                           (patient_id,)).fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------------------------
# Assessment CRUD
# ---------------------------------------------------------------------------

def save_assessment(data: dict) -> int:
    cols = [k for k in data.keys()]
    placeholders = ", ".join("?" for _ in cols)
    col_names = ", ".join(cols)
    vals = [data[c] for c in cols]
    with get_connection() as conn:
        cur = conn.execute(
            f"INSERT INTO assessments ({col_names}) VALUES ({placeholders})", vals
        )
        return cur.lastrowid


def get_assessments(patient_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date",
            (patient_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_latest_assessment(patient_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date DESC LIMIT 1",
            (patient_id,)
        ).fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

def save_alert(patient_id: int, message: str, severity: str = "warning",
               assessment_id: Optional[int] = None) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO alerts (patient_id, assessment_id, severity, message) VALUES (?, ?, ?, ?)",
            (patient_id, assessment_id, severity, message)
        )
        return cur.lastrowid


def get_active_alerts(patient_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE patient_id = ? AND resolved = 0 ORDER BY alert_date DESC",
            (patient_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def resolve_alert(alert_id: int) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE alerts SET resolved = 1 WHERE alert_id = ?", (alert_id,))
