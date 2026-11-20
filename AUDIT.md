# Engineering Audit: Email Automation & Reminder System

**Project Context:**
- **What it does / who it's for:** An automated email notification and recurring task reminder service that expands RFC 5545 `RRULE` schedules, populates personalized Jinja2 HTML templates, respects user opt-out flags, and logs dispatch audits to SQLite and CSV.
- **Stack & entry points:** Python 3.14 / 3.11, `jinja2`, `python-dateutil`, `pandas`, `sqlite3`, `fastapi`, `streamlit`. Entry points: `python main.py`, `python run_worker.py`, `python -m uvicorn api.app:app`, `python -m streamlit run app_streamlit.py`.
- **Real usage:** Batch scheduled runner (`main.py` / `run_worker.py`) + REST API (`api/app.py`) + audit dashboard (`app_streamlit.py`).
- **Constraint:** Preserve `data/contacts.csv` and `data/reminders.csv` schemas, `db/schema.sql`, and FastAPI endpoint signatures.

---

## Findings & Technical Debt

### 🔴 Critical Findings
1. **$O(N \times M \times K)$ Blocking Synchronous Database & Network I/O Loop (`main.py`):**
   - For every reminder $N$, for every occurrence $M$, for every contact $K$, the script executes:
     - Sequential Jinja2 template loading and rendering
     - Synchronous blocking `smtplib.SMTP` call (with 10-second timeout per recipient)
     - Individual single-row SQLite `INSERT INTO message_logs` execution
   - If sending to 500 contacts for a weekly recurring reminder (4 occurrences), the process blocks for up to thousands of seconds sequentially. A single network lag locks the entire batch.
2. **Fragile Date Parsing Vulnerable to Formatting Discrepancies (`src/scheduler.py`):**
   - `expand_schedule()` strictly parses timestamps via `datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")`. Any ISO 8601 string (`2026-11-20T19:00:00Z`), date-only string (`2026-11-20`), or timestamp missing seconds immediately crashes the entire batch pipeline.
3. **No Schema Validation on Contact and Reminder CSV Inputs (`main.py`):**
   - CSV files are loaded via raw `pd.read_csv()`. Missing expected columns (`email`, `unsubscribed`, `rrule`, `template_name`) cause unhandled `KeyError` crashes in the middle of a multi-recipient dispatch run without rollback or error recovery.

### 🟡 High Priority Findings
4. **Lack of Rate Limiting and Batching in Mailer (`src/mailer.py`):**
   - No rate limiting or delay throttling. If dry-run is turned off, attempting to send hundreds of messages simultaneously will trigger SMTP connection bans from mail providers (Gmail/SendGrid/SES).
5. **No Centralized Settings Configuration:**
   - Configuration is fragmented between environment variables (`os.getenv("DRY_RUN")`), hardcoded paths, and default arguments in `send_email()`. Needs centralized Pydantic settings.
6. **No Proper Worker Queue Architecture (`run_worker.py`):**
   - `run_worker.py` is simply a 7-line wrapper that calls `main()`. It lacks daemonization, polling intervals, graceful SIGINT/SIGTERM shutdown, and error alerting.

### 🟢 Nice-to-Have / Polish
7. **Tracking Webhooks Lack Persistence (`src/webhooks.py`):**
   - Open and click tracking endpoints return the pixel/redirect immediately, but do not record the interaction in `message_logs`.
8. **Missing Fast Path in Test Suite:**
   - Tests execute in one monolithic run without markers for fast mock tests vs I/O integration tests.

---

## What "Elite" Looks Like for This Exact Project

An elite notification & reminder engine:
- Employs resilient, multi-format datetime parsing (ISO 8601, flexible RFC formats).
- Validates contact and reminder schemas using Pydantic models before initiating any dispatch pass.
- Batches database inserts using `executemany` or transactions instead of individual loop queries.
- Manages SMTP connections via connection pooling or rate-limited dispatchers with exponential backoff on transient network failures.
- Packages clean configuration via `pyproject.toml`, structured JSON logging, and full test coverage for edge-case RRULE expansions.
