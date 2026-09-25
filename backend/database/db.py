import sqlite3
import os
import uuid
import json
import logging
from threading import local
from config import Config
import requests

logger = logging.getLogger(__name__)

_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "spp.db")
_local = local()


def _conn():
    if not hasattr(_local, "conn") or _local.conn is None:
        os.makedirs(os.path.dirname(_db_path), exist_ok=True)
        _local.conn = sqlite3.connect(_db_path, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_db():
    conn = _conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, role TEXT DEFAULT 'faculty',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY, student_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
            department TEXT NOT NULL, semester INTEGER NOT NULL, age INTEGER NOT NULL,
            gender TEXT NOT NULL, attendance REAL NOT NULL, study_hours REAL NOT NULL,
            assignment_score REAL NOT NULL, internal_marks REAL NOT NULL,
            previous_marks REAL NOT NULL, created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY, file_name TEXT NOT NULL, rows INTEGER DEFAULT 0,
            columns INTEGER DEFAULT 0, uploaded_by TEXT,
            uploaded_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS predictions (
            id TEXT PRIMARY KEY, student_id TEXT, student_name TEXT, department TEXT,
            semester INTEGER, attendance REAL, study_hours REAL, assignment_score REAL,
            internal_marks REAL, previous_marks REAL, predicted_marks REAL,
            predicted_score REAL, grade TEXT, performance TEXT, performance_level TEXT,
            risk_level TEXT, recommendation TEXT, risk_factors TEXT, recommendations TEXT,
            target_values TEXT, algorithm TEXT, accuracy REAL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY, report_name TEXT NOT NULL, report_type TEXT NOT NULL,
            generated_by TEXT, data TEXT, created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS ml_models (
            id TEXT PRIMARY KEY, model_name TEXT NOT NULL, algorithm TEXT NOT NULL,
            accuracy REAL, precision REAL, recall REAL, f1_score REAL, mae REAL,
            rmse REAL, r2_score REAL, file_path TEXT, is_active INTEGER DEFAULT 0,
            trained_by TEXT, created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()

    # Dynamic migrations for any existing databases
    existing_cols = [r[1] for r in c.execute("PRAGMA table_info(predictions)").fetchall()]
    migration_cols = {
        "predicted_score": "REAL",
        "performance_level": "TEXT",
        "risk_factors": "TEXT",
        "recommendations": "TEXT",
        "target_values": "TEXT",
        "algorithm": "TEXT",
        "accuracy": "REAL"
    }
    for col, col_type in migration_cols.items():
        if col not in existing_cols:
            try:
                c.execute(f"ALTER TABLE predictions ADD COLUMN {col} {col_type}")
                conn.commit()
            except Exception:
                pass

    # Ensure demo user and initial sample records exist if empty
    seed_initial_data()


def seed_initial_data():
    """
    Seeds initial demo user, students, and predictions so that
    the system has rich, realistic data right out of the box.
    """
    try:
        conn = _conn()
        c = conn.cursor()

        # 1. Seed demo user if no users exist
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            import bcrypt
            pwd = "password123"
            hashed = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            c.execute(
                "INSERT INTO users (id, name, email, password, role) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), "Faculty Admin", "admin@edupredict.ai", hashed, "admin")
            )
            c.execute(
                "INSERT INTO users (id, name, email, password, role) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), "Prof. Sarah Jenkins", "faculty@edupredict.ai", hashed, "faculty")
            )
            conn.commit()

        # 2. Seed students if no students exist
        c.execute("SELECT COUNT(*) FROM students")
        if c.fetchone()[0] == 0:
            dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets", "student_dataset.csv")
            if os.path.exists(dataset_path):
                import pandas as pd
                df = pd.read_csv(dataset_path)
                # Insert first 50 students into database
                for _, row in df.head(50).iterrows():
                    c.execute("""
                        INSERT OR IGNORE INTO students (
                            id, student_id, name, department, semester, age, gender,
                            attendance, study_hours, assignment_score, internal_marks, previous_marks
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        str(row["student_id"]),
                        str(row["name"]),
                        str(row["department"]),
                        int(row["semester"]),
                        int(row["age"]),
                        str(row["gender"]),
                        float(row["attendance"]),
                        float(row["study_hours"]),
                        float(row["assignment_score"]),
                        float(row["internal_marks"]),
                        float(row["previous_marks"])
                    ))
                conn.commit()

        # 3. Seed sample predictions if empty
        c.execute("SELECT COUNT(*) FROM predictions")
        if c.fetchone()[0] == 0:
            c.execute("SELECT * FROM students LIMIT 20")
            students_sample = [dict(r) for r in c.fetchall()]
            from services.prediction_service import predict_student_performance
            for s in students_sample:
                try:
                    predict_student_performance({
                        "student_id": s["student_id"],
                        "student_name": s["name"],
                        "department": s["department"],
                        "semester": s["semester"],
                        "attendance": s["attendance"],
                        "assignment_score": s["assignment_score"],
                        "internal_marks": s["internal_marks"],
                        "previous_marks": s["previous_marks"],
                        "study_hours": s["study_hours"],
                        "algorithm": "Random Forest Regressor"
                    })
                except Exception:
                    pass

    except Exception as e:
        logger.error(f"Error seeding initial data: {e}")


import threading

def _async_supabase_worker(table, data):
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        return
    try:
        endpoint = f"{url.rstrip('/')}/rest/v1/{table}"
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        requests.post(endpoint, json=data, headers=headers, timeout=1.5)
    except Exception:
        pass


def sync_to_supabase(table, data):
    """
    Spawns background daemon thread to sync to Supabase without blocking SQLite operations.
    """
    t = threading.Thread(target=_async_supabase_worker, args=(table, dict(data)), daemon=True)
    t.start()


class Result:
    def __init__(self, data=None, count=0):
        self.data = data or []
        self.count = count


def _all(table, order=None, desc=True, limit=None):
    cur = _conn().cursor()
    sql = f"SELECT * FROM {table}"
    if order:
        sql += f" ORDER BY {order} {'DESC' if desc else 'ASC'}"
    if limit:
        sql += f" LIMIT {limit}"
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    return Result(rows, len(rows))


def _find(table, col, val):
    cur = _conn().cursor()
    cur.execute(f"SELECT * FROM {table} WHERE {col} = ?", [val])
    rows = [dict(r) for r in cur.fetchall()]
    return Result(rows, len(rows))


def _search(table, search_term, search_cols, order="created_at", desc=True, page=1, per_page=20, filters=None):
    cur = _conn().cursor()
    where_parts = []
    params = []
    if search_term:
        or_parts = [f"{col} LIKE ?" for col in search_cols]
        where_parts.append(f"({' OR '.join(or_parts)})")
        for _ in search_cols:
            params.append(f"%{search_term}%")
    if filters:
        for col, val in filters.items():
            if val:
                where_parts.append(f"{col} = ?")
                params.append(val)
    where = ""
    if where_parts:
        where = " WHERE " + " AND ".join(where_parts)
    count_sql = f"SELECT COUNT(*) as cnt FROM {table}{where}"
    cur.execute(count_sql, params)
    total = cur.fetchone()[0]
    offset = (page - 1) * per_page
    sql = f"SELECT * FROM {table}{where} ORDER BY {order} {'DESC' if desc else 'ASC'} LIMIT {per_page} OFFSET {offset}"
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    return Result(rows, total)


def _insert(table, data):
    data = dict(data)
    if "id" not in data:
        data["id"] = str(uuid.uuid4())
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    _conn().cursor().execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(data.values()))
    _conn().commit()

    # Attempt Supabase sync
    try:
        sync_to_supabase(table, data)
    except Exception:
        pass

    return _find(table, "id", data["id"])


def _update(table, col, val, data):
    set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
    _conn().cursor().execute(f"UPDATE {table} SET {set_clause} WHERE {col} = ?", list(data.values()) + [val])
    _conn().commit()


def _delete(table, col, val):
    _conn().cursor().execute(f"DELETE FROM {table} WHERE {col} = ?", [val])
    _conn().commit()


def check_db_health():
    """
    Checks database health status without exposing credentials.
    Tests Supabase connection and local database persistence.
    """
    local_ok = False
    supabase_ok = False

    # 1. Test local database query
    try:
        cur = _conn().cursor()
        cur.execute("SELECT COUNT(*) FROM students")
        _ = cur.fetchone()
        local_ok = True
    except Exception as e:
        logger.error(f"Local database check failed: {e}")

    # 2. Test Supabase API connection
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_SERVICE_KEY", "")
    if url and key:
        try:
            res = requests.get(
                f"{url.rstrip('/')}/auth/v1/health",
                headers={"apikey": key},
                timeout=3.0
            )
            if res.status_code == 200:
                supabase_ok = True
        except Exception as e:
            logger.warning(f"Supabase connection check failed: {e}")

    is_connected = local_ok or supabase_ok
    status = "ok" if is_connected else "error"
    db_status = "connected" if is_connected else "disconnected"

    return {
        "status": status,
        "database": db_status,
        "supabase": "connected" if supabase_ok else "disconnected",
        "local_storage": "connected" if local_ok else "disconnected"
    }