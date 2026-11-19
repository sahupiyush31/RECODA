import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "database", "datafix.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Datasets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        upload_time TEXT NOT NULL,
        total_records INTEGER DEFAULT 0,
        total_columns INTEGER DEFAULT 0,
        columns TEXT, -- JSON array
        green_count INTEGER DEFAULT 0,
        red_count INTEGER DEFAULT 0,
        green_percentage REAL DEFAULT 0.0,
        red_percentage REAL DEFAULT 0.0,
        analysis_status TEXT DEFAULT 'pending',
        original_file_path TEXT NOT NULL,
        working_file_path TEXT NOT NULL
    )
    """)

    # Records metadata table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS records_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_id TEXT NOT NULL,
        record_index INTEGER NOT NULL,
        datafix_serial TEXT NOT NULL,
        human_required INTEGER NOT NULL, -- 0 for false, 1 for true
        validation_status TEXT NOT NULL,
        issues TEXT, -- JSON array of issue objects
        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_dataset ON records_metadata(dataset_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_serial ON records_metadata(dataset_id, datafix_serial)")

    # Audit logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_id TEXT NOT NULL,
        datafix_serial TEXT NOT NULL,
        column_name TEXT NOT NULL,
        old_value TEXT,
        new_value TEXT,
        actor TEXT NOT NULL, -- 'AI' or 'Human'
        reason TEXT,
        timestamp TEXT NOT NULL,
        validation_result TEXT,
        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_dataset ON audit_logs(dataset_id)")

    # Activity events table (Section 3.7 Recent Activity)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        description TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_dataset ON activity_logs(dataset_id)")

    conn.commit()
    conn.close()

# Helper DB functions
def insert_dataset(dataset_dict: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO datasets (
        id, filename, file_type, upload_time, total_records, total_columns,
        columns, green_count, red_count, green_percentage, red_percentage,
        analysis_status, original_file_path, working_file_path
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        dataset_dict["id"],
        dataset_dict["filename"],
        dataset_dict["file_type"],
        dataset_dict["upload_time"],
        dataset_dict.get("total_records", 0),
        dataset_dict.get("total_columns", 0),
        json.dumps(dataset_dict.get("columns", [])),
        dataset_dict.get("green_count", 0),
        dataset_dict.get("red_count", 0),
        dataset_dict.get("green_percentage", 0.0),
        dataset_dict.get("red_percentage", 0.0),
        dataset_dict.get("analysis_status", "pending"),
        dataset_dict["original_file_path"],
        dataset_dict["working_file_path"]
    ))
    conn.commit()
    conn.close()

def update_dataset_stats(dataset_id: str, total_records: int, total_columns: int, columns: List[str],
                         green_count: int, red_count: int, green_pct: float, red_pct: float, status: str = "analyzed"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE datasets SET
        total_records = ?,
        total_columns = ?,
        columns = ?,
        green_count = ?,
        red_count = ?,
        green_percentage = ?,
        red_percentage = ?,
        analysis_status = ?
    WHERE id = ?
    """, (
        total_records, total_columns, json.dumps(columns),
        green_count, red_count, green_pct, red_pct, status, dataset_id
    ))
    conn.commit()
    conn.close()

def get_dataset(dataset_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    if d.get("columns"):
        d["columns"] = json.loads(d["columns"])
    return d

def save_record_metadata_batch(dataset_id: str, records_meta: List[Dict[str, Any]]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM records_metadata WHERE dataset_id = ?", (dataset_id,))
    
    params = []
    for r in records_meta:
        params.append((
            dataset_id,
            r["record_index"],
            r["datafix_serial"],
            1 if r["human_required"] else 0,
            r["validation_status"],
            json.dumps(r.get("issues", []))
        ))
    cursor.executemany("""
    INSERT INTO records_metadata (dataset_id, record_index, datafix_serial, human_required, validation_status, issues)
    VALUES (?, ?, ?, ?, ?, ?)
    """, params)
    conn.commit()
    conn.close()

def get_records_metadata(dataset_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM records_metadata WHERE dataset_id = ? ORDER BY record_index ASC", (dataset_id,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for row in rows:
        r = dict(row)
        r["human_required"] = bool(r["human_required"])
        r["issues"] = json.loads(r["issues"]) if r.get("issues") else []
        res.append(r)
    return res

def log_audit(dataset_id: str, serial: str, col: str, old_val: Any, new_val: Any, actor: str, reason: str, val_result: str = "passed"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO audit_logs (dataset_id, datafix_serial, column_name, old_value, new_value, actor, reason, timestamp, validation_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        dataset_id,
        serial,
        col,
        str(old_val) if old_val is not None else "",
        str(new_val) if new_val is not None else "",
        actor,
        reason,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        val_result
    ))
    conn.commit()
    conn.close()

def get_audit_trail(dataset_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs WHERE dataset_id = ? ORDER BY id DESC", (dataset_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def log_activity(dataset_id: str, event_type: str, description: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO activity_logs (dataset_id, event_type, description, timestamp)
    VALUES (?, ?, ?, ?)
    """, (
        dataset_id,
        event_type,
        description,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def get_recent_activities(dataset_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activity_logs WHERE dataset_id = ? ORDER BY id DESC LIMIT ?", (dataset_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
