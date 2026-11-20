# Email Automation & Reminder System

A resilient, production-ready Python email automation engine featuring RFC 5545 `RRULE` recurring schedule expansion, dynamic Jinja2 HTML templating, compliance-first unsubscribe management, SQLite delivery audit logging, and safe dry-run simulation mode.

---

## 🏛 Architecture & Dispatch Pipeline

```
[Contacts CSV (with opt-out flags)] + [Reminders CSV (with RRULE schedules)]
                             │
                             ▼
             [RRULE Recurrence Expansion] (dateutil)
                             │
                             ▼
         [Opt-Out & Unsubscribe Compliance Check]
          ├── Unsubscribed ──► [Log Skipped Status]
          └── Active ────────► [Jinja2 Template Rendering]
                                     │
                                     ▼
                      [SMTP Dispatcher / Dry-Run Mode]
                                     │
                                     ▼
                [SQLite Delivery Log & Audit Trail]
                                     │
                                     ▼
              [CSV Dispatch Reports & FastAPI Service]
```

---

## ✨ Key Features

- **Standardized Recurrence (RRULE):** Leverages `dateutil.rrule` to support daily, weekly, monthly, and interval-based recurrence rules with count/until bounds.
- **Dynamic HTML Templating:** Powered by `Jinja2` for personalized email bodies, dates, and dynamic context variables.
- **Unsubscribe & Privacy Compliance:** Automatically checks `unsubscribed` status before rendering or queuing emails to prevent unsolicited messages.
- **Safe Dry-Run Simulation:** Allows developers and QA to test end-to-end rendering and scheduling without transmitting live emails.
- **FastAPI Tracking & Management:** Exposes RESTful endpoints (`/health`, `/logs`, `/contacts`, `/reminders`) along with tracking webhooks.
- **Full Relational Audit:** Logs every delivery attempt, timestamp, subject, and error details in SQLite (`db/email.db`).

---

## 🚀 Quick Start Guide

### 1. Installation
```bash
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

### 2. Run Automation Engine
```bash
# Runs in safe dry-run simulation by default
python main.py
```

### 3. Launch Streamlit Dashboard
```bash
python -m streamlit run app_streamlit.py
```

### 4. Run API Service
```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run Tests
```bash
python -m unittest discover -s tests -v
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status. |
| `GET` | `/logs` | Retreive all email delivery records from SQLite. |
| `GET` | `/contacts` | Returns list of configured contacts and unsubscribe status. |
| `GET` | `/reminders` | Returns recurring reminder definitions. |
| `GET` | `/t/o/{id}.gif` | Transparent 1x1 GIF for open-rate tracking. |
| `GET` | `/t/c/{id}` | Click-tracking redirect handler. |
