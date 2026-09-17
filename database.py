"""
=============================================================================
Database Module - SQLite
Hospital Laboratory Report Integrity Verification System
=============================================================================
Author: Educational Lab Project
Purpose: Manage SQLite storage for laboratory reports and verification history.
         Implements parameterized queries to prevent SQL injection.
=============================================================================
"""

import os
import sqlite3
from datetime import datetime

# Absolute path to database file
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
DB_PATH = os.path.join(DB_DIR, "hospital_crc.db")


def get_db_connection():
    """
    Establishes and returns a connection to the SQLite database.
    Configures row_factory so columns can be accessed by name like dictionaries.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initializes database tables if they don't already exist.
    Also seeds initial synthetic sample reports if the database is empty.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Laboratory Reports Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS laboratory_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT UNIQUE NOT NULL,
            patient_name TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            department TEXT NOT NULL,
            test_name TEXT NOT NULL,
            test_result TEXT NOT NULL,
            unit TEXT NOT NULL,
            reference_range TEXT NOT NULL,
            report_date TEXT NOT NULL,
            clinical_notes TEXT,
            original_data TEXT NOT NULL,
            original_crc TEXT NOT NULL,
            crc_polynomial TEXT NOT NULL DEFAULT 'CRC-16-CCITT',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Verification History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT NOT NULL,
            patient_name TEXT NOT NULL,
            test_name TEXT NOT NULL,
            original_crc TEXT NOT NULL,
            received_crc TEXT NOT NULL,
            transmission_type TEXT NOT NULL,
            what_changed TEXT,
            received_data TEXT NOT NULL,
            verification_status TEXT NOT NULL, -- 'ACCEPTED' or 'REJECTED'
            is_corrupted INTEGER NOT NULL,     -- 0 for valid, 1 for corrupted
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    # Seed sample reports if none exist
    seed_initial_data()


def serialize_report_data(report_id, patient_name, patient_id, department, test_name, test_result, unit, reference_range, report_date):
    """
    Converts laboratory report fields into a standardized transmission payload string.
    Format:
    REPORT_ID:LAB001|PATIENT:Anil Kumar|PAT_ID:PID-9821|DEPT:Biochemistry|TEST:Blood Glucose|RESULT:95|UNIT:mg/dL|RANGE:70-100|DATE:2026-09-16
    """
    return (
        f"REPORT_ID:{report_id}|"
        f"PATIENT:{patient_name}|"
        f"PAT_ID:{patient_id}|"
        f"DEPT:{department}|"
        f"TEST:{test_name}|"
        f"RESULT:{test_result}|"
        f"UNIT:{unit}|"
        f"RANGE:{reference_range}|"
        f"DATE:{report_date}"
    )


def seed_initial_data():
    """
    Seeds initial synthetic laboratory reports for beginner demonstration.
    """
    from crc import calculate_crc

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM laboratory_reports")
    count = cursor.fetchone()["cnt"]

    if count == 0:
        samples = [
            {
                "report_id": "LAB-1001",
                "patient_name": "Synthetic Patient Alpha",
                "patient_id": "SYN-501",
                "department": "Biochemistry",
                "test_name": "Fasting Blood Glucose",
                "test_result": "95",
                "unit": "mg/dL",
                "reference_range": "70 - 100",
                "report_date": "2026-09-16",
                "clinical_notes": "Routine diabetic checkup. Fasting sample within normal parameters."
            },
            {
                "report_id": "LAB-1002",
                "patient_name": "Synthetic Patient Beta",
                "patient_id": "SYN-502",
                "department": "Hematology",
                "test_name": "Hemoglobin (Hb)",
                "test_result": "13.8",
                "unit": "g/dL",
                "reference_range": "12.0 - 16.0",
                "report_date": "2026-09-16",
                "clinical_notes": "Pre-operative complete blood count."
            },
            {
                "report_id": "LAB-1003",
                "patient_name": "Synthetic Patient Gamma",
                "patient_id": "SYN-503",
                "department": "Clinical Pathology",
                "test_name": "Serum Creatinine",
                "test_result": "1.05",
                "unit": "mg/dL",
                "reference_range": "0.7 - 1.3",
                "report_date": "2026-09-16",
                "clinical_notes": "Renal function evaluation."
            }
        ]

        for s in samples:
            payload = serialize_report_data(
                s["report_id"], s["patient_name"], s["patient_id"],
                s["department"], s["test_name"], s["test_result"],
                s["unit"], s["reference_range"], s["report_date"]
            )
            crc_result = calculate_crc(payload, "CRC-16")
            cursor.execute("""
                INSERT INTO laboratory_reports (
                    report_id, patient_name, patient_id, department,
                    test_name, test_result, unit, reference_range,
                    report_date, clinical_notes, original_data, original_crc, crc_polynomial
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                s["report_id"], s["patient_name"], s["patient_id"],
                s["department"], s["test_name"], s["test_result"],
                s["unit"], s["reference_range"], s["report_date"],
                s["clinical_notes"], payload, crc_result["crc_hex"], crc_result["polynomial"]
            ))

        conn.commit()

    conn.close()


def insert_report(data: dict) -> bool:
    """
    Inserts a newly created laboratory report into the database using parameterized queries.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO laboratory_reports (
                report_id, patient_name, patient_id, department,
                test_name, test_result, unit, reference_range,
                report_date, clinical_notes, original_data, original_crc, crc_polynomial
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["report_id"],
            data["patient_name"],
            data["patient_id"],
            data["department"],
            data["test_name"],
            data["test_result"],
            data["unit"],
            data["reference_range"],
            data["report_date"],
            data.get("clinical_notes", ""),
            data["original_data"],
            data["original_crc"],
            data.get("crc_polynomial", "CRC-16-CCITT")
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_all_reports():
    """
    Retrieves all laboratory reports ordered by creation date descending.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM laboratory_reports ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_report_by_id(report_id: str):
    """
    Fetches a specific laboratory report by its unique report_id.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM laboratory_reports WHERE report_id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def insert_verification(record: dict) -> int:
    """
    Inserts a verification attempt log into verification_history.
    Returns the new verification ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO verification_history (
            report_id, patient_name, test_name, original_crc,
            received_crc, transmission_type, what_changed,
            received_data, verification_status, is_corrupted
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record["report_id"],
        record.get("patient_name", "Unknown"),
        record.get("test_name", "Unknown"),
        record["original_crc"],
        record["received_crc"],
        record["transmission_type"],
        record.get("what_changed", "None"),
        record["received_data"],
        record["verification_status"],
        1 if record["is_corrupted"] else 0
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_verification_history(limit: int = 100):
    """
    Retrieves the verification history ordered by latest first.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM verification_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_verification_by_id(v_id: int):
    """
    Retrieves a single verification record by its ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM verification_history WHERE id = ?", (v_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_dashboard_stats():
    """
    Calculates summary statistics for the dashboard cards.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM laboratory_reports")
    total_reports = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM verification_history")
    total_verifications = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM verification_history WHERE verification_status = 'ACCEPTED'")
    accepted_verifications = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM verification_history WHERE verification_status = 'REJECTED'")
    rejected_verifications = cursor.fetchone()["cnt"]

    # Recent 5 verifications
    cursor.execute("SELECT * FROM verification_history ORDER BY id DESC LIMIT 5")
    recent_verifications = [dict(row) for row in cursor.fetchall()]

    # Recent 5 reports
    cursor.execute("SELECT * FROM laboratory_reports ORDER BY id DESC LIMIT 5")
    recent_reports = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "total_reports": total_reports,
        "total_verifications": total_verifications,
        "accepted_verifications": accepted_verifications,
        "rejected_verifications": rejected_verifications,
        "recent_verifications": recent_verifications,
        "recent_reports": recent_reports
    }


def delete_report(report_id: str) -> bool:
    """
    Deletes a report by report_id (utility function for lab reset).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM laboratory_reports WHERE report_id = ?", (report_id,))
    cursor.execute("DELETE FROM verification_history WHERE report_id = ?", (report_id,))
    conn.commit()
    conn.close()
    return True


def clear_all_history() -> bool:
    """
    Clears verification history table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM verification_history")
    conn.commit()
    conn.close()
    return True
