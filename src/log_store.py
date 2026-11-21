"""
Delivery log in SQLite.

Every attempt is recorded (sent / failed / skipped). A UNIQUE constraint on
(reminder, recipient, occurrence date) guarantees nobody gets the same
reminder twice, even if the script runs every few minutes.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS deliveries (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    reminder_id   TEXT NOT NULL,
    title         TEXT NOT NULL,
    category      TEXT NOT NULL,
    recipient     TEXT NOT NULL,
    email         TEXT NOT NULL,
    occurrence    TEXT NOT NULL,      -- due date of this occurrence (YYYY-MM-DD)
    status        TEXT NOT NULL,      -- sent / dry-run / failed / skipped
    detail        TEXT,
    mode          TEXT,
    created_at    TEXT NOT NULL,
    UNIQUE (reminder_id, email, occurrence, status)
);
"""


class DeliveryLog:
    def __init__(self, path: Path = DB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.executescript(SCHEMA)

    def already_sent(self, reminder_id: str, email: str, occurrence: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM deliveries WHERE reminder_id=? AND email=? AND occurrence=? AND status IN ('sent','dry-run')",
            (reminder_id, email, occurrence)).fetchone()
        return row is not None

    def record(self, reminder_id: str, title: str, category: str, recipient: str, email: str,
               occurrence: str, status: str, detail: str, mode: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO deliveries (reminder_id,title,category,recipient,email,occurrence,status,detail,mode,created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (reminder_id, title, category, recipient, email, occurrence, status, detail, mode,
             datetime.now().isoformat(timespec="seconds")))
        self.conn.commit()

    def to_dataframe(self) -> pd.DataFrame:
        return pd.read_sql_query("SELECT * FROM deliveries ORDER BY id DESC", self.conn)

    def close(self) -> None:
        self.conn.close()
