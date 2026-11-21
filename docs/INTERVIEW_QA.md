# Interview Preparation: Email Automation & Reminder System

### 1. Explain your project.

**HR version:** I built a system that automatically sends reminder emails: bill due dates, meetings,
deadlines, renewals, even birthday wishes. You add reminders and contacts once, and it sends a personalised,
professional-looking email to the right people at the right time. It keeps a record of every email and makes
sure nobody gets the same reminder twice. There's also a dashboard to manage everything without touching code.

**Technical version:** It's a Python scheduling and notification pipeline. Contacts and reminders come from CSV
files and are validated with regex and date parsing. A scheduler computes the next occurrence of each reminder
from its repeat rule and lead time, including month-end edge cases. Due items are rendered with Jinja2 template
inheritance into HTML plus a plain-text fallback, built as a multipart `EmailMessage`, and sent through
`smtplib` with STARTTLS and retries, or saved as `.eml` files in dry-run mode. Every attempt goes into SQLite,
and the check on reminder, email and occurrence makes re-runs idempotent. I built a Rich CLI and a Streamlit
control centre, and wrote 16 pytest tests.

### 2. How does Python send an email?

`smtplib` connects to an SMTP server (for Gmail, `smtp.gmail.com` on port 587). The connection is upgraded to
encrypted TLS with `starttls()`, the program logs in with `login()`, and `send_message()` sends an
`EmailMessage` object that holds the headers (From, To, Subject) and the body.

### 3. Why does Gmail need an App Password?

Google blocks normal passwords for programmatic SMTP logins. With 2-step verification on, you create a
16-character App Password that only works for that app and can be revoked at any time. It goes in `.env`,
never in the code.

### 4. Why send both HTML and plain text?

Some email clients, screen readers and spam filters prefer plain text. A multipart/alternative message carries
both, and the client chooses. Including a text part also improves deliverability.

### 5. Why inline CSS in the templates?

Gmail and Outlook remove `<style>` blocks and external stylesheets. Inline styles and table-based layout are
the reliable way to make HTML emails look the same everywhere.

### 6. How do you prevent duplicate emails?

Every delivery is logged in SQLite with the reminder id, recipient email and occurrence date. Before sending,
the engine checks whether that combination was already sent. So the script can safely run every 15 minutes
from Task Scheduler or cron, and each person gets each reminder once.

### 7. How do repeat rules work, and what edge cases did you handle?

Daily, weekly, monthly and yearly. Weekly uses a ceiling division on the day difference. For monthly I wrote
`add_months()`, which clamps to the last valid day, so a bill on 31 January repeats on 28 February (29 in leap
years), not 3 March. Birthdays on 29 February are celebrated on 28 February in non-leap years. All of these
have tests.

### 8. What happens if one email fails?

Each recipient is handled independently inside a try/except. A failure is logged with the error message and
the loop continues. Network errors are retried with exponential backoff (2, 4, 8 seconds). Authentication
errors are not retried, because retrying won't fix a wrong password, and the user gets a clear message instead.

### 9. How do you handle bad data?

Contacts with invalid emails are rejected at load time with the row number and reason. Bad dates, unknown
categories and unknown repeat values are reported and either skipped or replaced with safe defaults. The
program never crashes because of one bad row.

### 10. What is dry-run mode and why is it the default?

Dry-run saves each email as an `.eml` file plus an HTML preview instead of sending it. That makes testing safe,
since you can't spam real people by accident, and you can still see exactly what recipients would receive.

### 11. How would you run it automatically every day?

On Windows, Task Scheduler runs `python main.py run` every 15 minutes. On Linux or Mac, a cron job does the
same: `*/15 * * * * cd /path && venv/bin/python main.py run`. Or use the built-in `python main.py watch`.

### 12. How did you test date-based logic?

The scheduler takes the current time as a parameter instead of calling `datetime.now()` inside, so tests can
pass any date. The CLI's `--at` option and the dashboard date picker use the same idea for manual testing.

### 13. How would you scale this to 100,000 emails a day?

Move sending to a task queue (Celery with Redis), use a transactional email API (SendGrid, Amazon SES) with
rate limiting, store data in PostgreSQL, and add bounce and unsubscribe webhooks.

### 14. What did you learn?

How email actually works (SMTP, TLS, MIME), template engines, date arithmetic edge cases, idempotent design,
handling secrets safely, and building a practical dashboard on top of a back-end script.
