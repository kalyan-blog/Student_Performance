import sqlite3
import os
import uuid
import json
import logging
from threading import local
import requests

logger = logging.getLogger(__name__)

_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "spp.db")
_local = local()


def _get_database_url():
    return os.getenv("DATABASE_URL", "").strip()


def _try_pg_connection():
    db_url = _get_database_url()
    if not db_url or not db_url.startswith(("postgres://", "postgresql://")):
        return None
    try:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(db_url, connect_timeout=4)
        return conn
    except Exception as e:
        logger.warning(f"Supabase PostgreSQL connection failed: {e}")
        return None


def _sqlite_conn():
    if not hasattr(_local, "sqlite_conn") or _local.sqlite_conn is None:
        os.makedirs(os.path.dirname(_db_path), exist_ok=True)
        _local.sqlite_conn = sqlite3.connect(_db_path, check_same_thread=False)
        _local.sqlite_conn.row_factory = sqlite3.Row
        _local.sqlite_conn.execute("PRAGMA journal_mode=WAL")
        _local.sqlite_conn.execute("PRAGMA foreign_keys=ON")
    return _local.sqlite_conn


def _get_active_driver():
    if hasattr(_local, "pg_conn") and _local.pg_conn is not None:
        try:
            with _local.pg_conn.cursor() as cur:
                cur.execute("SELECT 1")
            return "postgres", _local.pg_conn
        except Exception:
            _local.pg_conn = None

    pg = _try_pg_connection()
    if pg:
        _local.pg_conn = pg
        return "postgres", pg
    return "sqlite", _sqlite_conn()


def init_db():
    # 1. Initialize SQLite (for local storage or fallback)
    conn_sq = _sqlite_conn()
    c_sq = conn_sq.cursor()
    c_sq.executescript("""
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
    conn_sq.commit()

    # Dynamic migrations for SQLite
    existing_cols = [r[1] for r in c_sq.execute("PRAGMA table_info(predictions)").fetchall()]
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
                c_sq.execute(f"ALTER TABLE predictions ADD COLUMN {col} {col_type}")
                conn_sq.commit()
            except Exception:
                pass

    # 2. Initialize PostgreSQL if reachable
    driver, conn = _get_active_driver()
    if driver == "postgres":
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL, role TEXT DEFAULT 'faculty',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS students (
                        id TEXT PRIMARY KEY, student_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
                        department TEXT NOT NULL, semester INTEGER NOT NULL, age INTEGER NOT NULL,
                        gender TEXT NOT NULL, attendance REAL NOT NULL, study_hours REAL NOT NULL,
                        assignment_score REAL NOT NULL, internal_marks REAL NOT NULL,
                        previous_marks REAL NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS datasets (
                        id TEXT PRIMARY KEY, file_name TEXT NOT NULL, rows INTEGER DEFAULT 0,
                        columns INTEGER DEFAULT 0, uploaded_by TEXT,
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS predictions (
                        id TEXT PRIMARY KEY, student_id TEXT, student_name TEXT, department TEXT,
                        semester INTEGER, attendance REAL, study_hours REAL, assignment_score REAL,
                        internal_marks REAL, previous_marks REAL, predicted_marks REAL,
                        predicted_score REAL, grade TEXT, performance TEXT, performance_level TEXT,
                        risk_level TEXT, recommendation TEXT, risk_factors TEXT, recommendations TEXT,
                        target_values TEXT, algorithm TEXT, accuracy REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS reports (
                        id TEXT PRIMARY KEY, report_name TEXT NOT NULL, report_type TEXT NOT NULL,
                        generated_by TEXT, data TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS ml_models (
                        id TEXT PRIMARY KEY, model_name TEXT NOT NULL, algorithm TEXT NOT NULL,
                        accuracy REAL, precision REAL, recall REAL, f1_score REAL, mae REAL,
                        rmse REAL, r2_score REAL, file_path TEXT, is_active INTEGER DEFAULT 0,
                        trained_by TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
        except Exception as e:
            logger.warning(f"PostgreSQL table initialization warning: {e}")
            conn.rollback()

    seed_initial_data()


def seed_initial_data():
    try:
        conn = _sqlite_conn()
        c = conn.cursor()

        # Seed demo user if no users exist
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

        # Seed students if empty
        c.execute("SELECT COUNT(*) FROM students")
        if c.fetchone()[0] == 0:
            dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets", "student_dataset.csv")
            if os.path.exists(dataset_path):
                import pandas as pd
                df = pd.read_csv(dataset_path)
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

        # Seed sample predictions if empty
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
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "") or os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_SERVICE_KEY", "")
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
        requests.post(endpoint, json=data, headers=headers, timeout=2.0)
    except Exception:
        pass


def sync_to_supabase(table, data):
    t = threading.Thread(target=_async_supabase_worker, args=(table, dict(data)), daemon=True)
    t.start()


class Result:
    def __init__(self, data=None, count=0):
        self.data = data or []
        self.count = count


def _all(table, order=None, desc=True, limit=None):
    driver, conn = _get_active_driver()
    if driver == "postgres":
        import psycopg2.extras
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            sql = f"SELECT * FROM {table}"
            if order:
                sql += f" ORDER BY {order} {'DESC' if desc else 'ASC'}"
            if limit:
                sql += f" LIMIT {limit}"
            cur.execute(sql)
            rows = [dict(r) for r in cur.fetchall()]
            return Result(rows, len(rows))
    else:
        cur = conn.cursor()
        sql = f"SELECT * FROM {table}"
        if order:
            sql += f" ORDER BY {order} {'DESC' if desc else 'ASC'}"
        if limit:
            sql += f" LIMIT {limit}"
        cur.execute(sql)
        rows = [dict(r) for r in cur.fetchall()]
        return Result(rows, len(rows))


def _find(table, col, val):
    driver, conn = _get_active_driver()
    if driver == "postgres":
        import psycopg2.extras
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {table} WHERE {col} = %s", [val])
            rows = [dict(r) for r in cur.fetchall()]
            return Result(rows, len(rows))
    else:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table} WHERE {col} = ?", [val])
        rows = [dict(r) for r in cur.fetchall()]
        return Result(rows, len(rows))


def _search(table, search_term, search_cols, order="created_at", desc=True, page=1, per_page=20, filters=None):
    driver, conn = _get_active_driver()
    placeholder = "%s" if driver == "postgres" else "?"
    where_parts = []
    params = []
    if search_term:
        or_parts = [f"{col} LIKE {placeholder}" for col in search_cols]
        where_parts.append(f"({' OR '.join(or_parts)})")
        for _ in search_cols:
            params.append(f"%{search_term}%")
    if filters:
        for col, val in filters.items():
            if val:
                where_parts.append(f"{col} = {placeholder}")
                params.append(val)
    where = ""
    if where_parts:
        where = " WHERE " + " AND ".join(where_parts)

    count_sql = f"SELECT COUNT(*) as cnt FROM {table}{where}"
    offset = (page - 1) * per_page
    sql = f"SELECT * FROM {table}{where} ORDER BY {order} {'DESC' if desc else 'ASC'} LIMIT {per_page} OFFSET {offset}"

    if driver == "postgres":
        import psycopg2.extras
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(count_sql, params)
            cnt_row = cur.fetchone()
            total = cnt_row["cnt"] if cnt_row else 0
            cur.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
            return Result(rows, total)
    else:
        cur = conn.cursor()
        cur.execute(count_sql, params)
        total = cur.fetchone()[0]
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        return Result(rows, total)


def _insert(table, data):
    data = dict(data)
    if "id" not in data:
        data["id"] = str(uuid.uuid4())
    cols = ", ".join(data.keys())

    driver, conn = _get_active_driver()
    if driver == "postgres":
        placeholders = ", ".join(["%s" for _ in data])
        with conn.cursor() as cur:
            cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(data.values()))
        conn.commit()
    else:
        placeholders = ", ".join(["?" for _ in data])
        conn.cursor().execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(data.values()))
        conn.commit()

    # Attempt Supabase REST sync
    try:
        sync_to_supabase(table, data)
    except Exception:
        pass

    return _find(table, "id", data["id"])


def _update(table, col, val, data):
    driver, conn = _get_active_driver()
    if driver == "postgres":
        set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
        with conn.cursor() as cur:
            cur.execute(f"UPDATE {table} SET {set_clause} WHERE {col} = %s", list(data.values()) + [val])
        conn.commit()
    else:
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        conn.cursor().execute(f"UPDATE {table} SET {set_clause} WHERE {col} = ?", list(data.values()) + [val])
        conn.commit()


def _delete(table, col, val):
    driver, conn = _get_active_driver()
    if driver == "postgres":
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {table} WHERE {col} = %s", [val])
        conn.commit()
    else:
        conn.cursor().execute(f"DELETE FROM {table} WHERE {col} = ?", [val])
        conn.commit()


def check_db_health():
    """
    Checks database health status without exposing credentials.
    Tests Supabase PostgreSQL connection, Supabase REST endpoint, and local persistence.
    Returns:
    { "status": "ok", "database": "connected" }
    or
    { "status": "error", "database": "disconnected" }
    """
    pg_ok = False
    supabase_ok = False
    local_ok = False

    # 1. Test PostgreSQL connection if DATABASE_URL configured
    db_url = _get_database_url()
    if db_url and db_url.startswith(("postgres://", "postgresql://")):
        try:
            import psycopg2
            conn = psycopg2.connect(db_url, connect_timeout=3)
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                _ = cur.fetchone()
            conn.close()
            pg_ok = True
        except Exception as e:
            logger.warning(f"PostgreSQL connection check: {e}")

    # 2. Test Supabase API endpoint
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "") or os.getenv("SUPABASE_KEY", "")
    if supabase_url and supabase_key:
        try:
            res = requests.get(
                f"{supabase_url.rstrip('/')}/auth/v1/health",
                headers={"apikey": supabase_key},
                timeout=3.0
            )
            if res.status_code == 200:
                supabase_ok = True
        except Exception as e:
            logger.warning(f"Supabase REST health check failed: {e}")

    # 3. Test local storage fallback
    try:
        cur = _sqlite_conn().cursor()
        cur.execute("SELECT COUNT(*) FROM students")
        _ = cur.fetchone()
        local_ok = True
    except Exception as e:
        logger.warning(f"Local storage check failed: {e}")

    is_connected = pg_ok or supabase_ok or local_ok
    status = "ok" if is_connected else "error"
    db_status = "connected" if is_connected else "disconnected"

    return {
        "status": status,
        "database": db_status
    }