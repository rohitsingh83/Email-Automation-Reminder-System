"""FastAPI service for Email Automation & Reminder System."""

from pathlib import Path
import sqlite3
import pandas as pd
from fastapi import FastAPI
from src.webhooks import router as webhooks_router

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="Email Automation & Reminder API", version="1.0.0")

# Mount open/click tracking webhooks
app.include_router(webhooks_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "Email-Automation-Reminder-System"}


@app.get("/logs")
def get_logs():
    conn = sqlite3.connect(str(ROOT / "db" / "email.db"))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT reminder_id, recipient_name, recipient_email, subject, status, error_detail, timestamp FROM message_logs ORDER BY id DESC").fetchall()
    conn.close()
    return {"logs": [dict(r) for r in rows]}


@app.get("/contacts")
def list_contacts():
    contacts_file = ROOT / "data" / "contacts.csv"
    if contacts_file.exists():
        df = pd.read_csv(contacts_file).fillna("")
        return {"contacts": df.to_dict(orient="records")}
    return {"contacts": []}


@app.get("/reminders")
def list_reminders():
    reminders_file = ROOT / "data" / "reminders.csv"
    if reminders_file.exists():
        df = pd.read_csv(reminders_file).fillna("")
        return {"reminders": df.to_dict(orient="records")}
    return {"reminders": []}
