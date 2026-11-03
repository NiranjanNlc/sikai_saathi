"""SQLite persistence for sessions, diagnoses, assessments and progress."""

import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS diagnoses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    problem_id TEXT NOT NULL,
    misconception TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    problem_id TEXT NOT NULL,
    answer REAL NOT NULL,
    correct INTEGER NOT NULL,
    error_type TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: str) -> None:
    conn = _connect(path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_diagnosis(path: str, student_id: str, problem_id: str,
                     misconception: str, confidence: float) -> None:
    conn = _connect(path)
    try:
        conn.execute(
            "INSERT INTO diagnoses (student_id, problem_id, misconception, confidence, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (student_id, problem_id, misconception, confidence, _now()),
        )
        conn.commit()
    finally:
        conn.close()


def record_assessment(path: str, student_id: str, problem_id: str,
                      answer: float, correct: bool, error_type: str) -> int:
    """Record an assessment attempt. Returns total attempts for this student+problem."""
    conn = _connect(path)
    try:
        conn.execute(
            "INSERT INTO assessments (student_id, problem_id, answer, correct, error_type, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (student_id, problem_id, answer, 1 if correct else 0, error_type, _now()),
        )
        conn.commit()
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM assessments WHERE student_id = ? AND problem_id = ?",
            (student_id, problem_id),
        ).fetchone()
        return int(row["n"])
    finally:
        conn.close()


MASTERY_NEEDED = 3


def practice_streak(path: str, student_id: str) -> int:
    """Consecutive correct answers on *practice* problems (newest first).

    Practice problems have '-p' in their id (see math_engine.generate_similar).
    The demo problem itself never counts toward the streak.
    """
    conn = _connect(path)
    try:
        rows = conn.execute(
            "SELECT correct FROM assessments"
            " WHERE student_id = ? AND problem_id LIKE '%-p%'"
            " ORDER BY id DESC",
            (student_id,),
        ).fetchall()
        streak = 0
        for r in rows:
            if int(r["correct"]) == 1:
                streak += 1
            else:
                break
        return streak
    finally:
        conn.close()


def student_has_mastery(path: str, student_id: str) -> bool:
    """Mastery = MASTERY_NEEDED correct practice answers in a row."""
    return practice_streak(path, student_id) >= MASTERY_NEEDED


def get_progress(path: str, student_id: str) -> dict:
    conn = _connect(path)
    try:
        d = conn.execute(
            "SELECT COUNT(*) AS n FROM diagnoses WHERE student_id = ?", (student_id,)
        ).fetchone()
        a = conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(correct), 0) AS c"
            " FROM assessments WHERE student_id = ?",
            (student_id,),
        ).fetchone()
        rows = conn.execute(
            "SELECT 'diagnosis' AS kind, problem_id, misconception AS detail, created_at"
            " FROM diagnoses WHERE student_id = ?"
            " UNION ALL "
            "SELECT 'assessment' AS kind, problem_id,"
            " (CASE WHEN correct = 1 THEN 'correct' ELSE error_type END) AS detail, created_at"
            " FROM assessments WHERE student_id = ?"
            " ORDER BY created_at DESC LIMIT 10",
            (student_id, student_id),
        ).fetchall()
        recent = [
            {"kind": r["kind"], "problem_id": r["problem_id"],
             "detail": r["detail"], "created_at": r["created_at"]}
            for r in rows
        ]
        return {
            "diagnoses": int(d["n"]),
            "assessments": int(a["n"]),
            "correct": int(a["c"]),
            "recent": recent,
        }
    finally:
        conn.close()
