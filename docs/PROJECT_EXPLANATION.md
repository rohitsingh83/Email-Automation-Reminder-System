# Project Explanation: Email Automation & Reminder System

## 1. What is it?

**Simple explanation.** People forget bills, renewals, meetings and deadlines. This program keeps a list of
reminders and contacts, checks what is due, and automatically sends a nicely designed, personalised email to
the right people at the right time. It also sends birthday wishes on its own. It keeps a log of every email,
so you can see what was sent, skipped or failed, and it never sends the same reminder twice.

**Technical explanation.** It's a scheduling and notification pipeline in Python. Contacts and reminders live
in CSV files and are validated on load. A scheduler computes the next occurrence of each reminder from its
repeat rule (daily, weekly, monthly or yearly, with month-end handling) and its lead time. Due reminders are
rendered with Jinja2 HTML templates (with a plain-text fallback) and sent over SMTP with STARTTLS or SSL and
retries, or saved as `.eml` files in dry-run mode. Every attempt is written to SQLite, and a uniqueness check
makes sending idempotent. A Streamlit dashboard manages everything visually.

### Why it matters

| Without automation | With this system |
|---|---|
| Someone has to remember to send every reminder | Reminders go out automatically on schedule |
| Copy-paste emails with wrong names | Every email is personalised from the contact list |
| No proof of what was sent | SQLite delivery log with status and timestamps |
| Same email sent twice by mistake | Duplicate protection per reminder, recipient and date |
| Unsubscribe requests ignored | Unsubscribed contacts are skipped and logged |

Companies use the same ideas in billing systems ("your invoice is due"), HR tools (onboarding emails), schools
(fee and exam reminders), clinics (appointment reminders) and marketing platforms (Mailchimp, SendGrid).

### Workflow

```
contacts.csv + reminders.csv → validate → find due reminders (repeat rules + lead time)
   → expand groups → skip unsubscribed / already-sent → render template → send (SMTP or dry-run)
   → write delivery log → dashboard and CSV report
```

## 2. Tech stack options

| Option | Tools | Difficulty | Output |
|---|---|---|---|
| A. Easy | smtplib, one hard-coded message, `time.sleep` loop | Beginner | Sends one fixed email |
| **B. Intermediate** ✅ | smtplib + email.message, Jinja2, Pandas, SQLite, python-dotenv, Rich, Streamlit | Intermediate | Personalised HTML emails, schedules, logs, dashboard |
| C. Advanced | B + Celery/Redis task queue, SendGrid/SES API, webhooks for opens/clicks, Docker | Advanced | Production-scale delivery with tracking |

**Chosen: B.** It uses Python's standard email libraries (which interviewers expect you to know), needs no paid
service, and can be run and tested safely in dry-run mode.

## 3. Architecture

```
  INPUT        data/contacts.csv       data/reminders.csv        templates/*.html       .env (SMTP)
                      │                        │                        │                  │
  PROCESSING   ┌──────▼────────────────────────▼──────┐                 │                  │
               │ data_loader.py  validate, parse,     │                 │                  │
               │                 expand group:team    │                 │                  │
               ├──────────────────────────────────────┤                 │                  │
               │ scheduler.py    next occurrence,     │                 │                  │
               │                 lead time, birthdays │                 │                  │
               ├──────────────────────────────────────┤                 │                  │
               │ engine.py       for each due item →  │◄── renderer.py ◄┘                  │
               │                 skip/duplicate check │    (Jinja2 HTML + text)            │
               │                 → render → send      │◄── mailer.py  ◄────────────────────┘
               │                 → log                │    (SMTP / dry-run)
               └──────────────────┬───────────────────┘
                                  │
  OUTPUT       log_store.py (SQLite) → outputs/delivery_log.csv
               outputs/sent_emails/*.eml + *.html (dry-run)
               main.py (CLI)  ·  app.py (Streamlit control centre)
```

### Key design decisions

* **Dry-run by default.** New users can't accidentally email real people. The `.eml` files open in
  Outlook or Thunderbird exactly as recipients would see them.
* **Idempotency.** The script can be run every 15 minutes by Task Scheduler or cron; the log guarantees each
  reminder occurrence reaches each person only once.
* **Send-time rules.** Reminders with a lead time go out at 08:00 on the send day; same-day reminders go out
  one hour before the event.
* **Month-end safety.** A monthly reminder on the 31st falls on 28/29 February, not 3 March.
* **Credentials in `.env`.** Passwords are never in the code or on GitHub (`.env` is in `.gitignore`).

## 4. Implementation plan

| Phase | What | Why | Output | Common mistakes |
|---|---|---|---|---|
| 1. Setup | venv, `pip install -r requirements.txt` | Reproducible environment | Libraries installed | Installing globally |
| 2. Folders | `data/ templates/ src/ outputs/ docs/ tests/` | Separate data, code, output | Project tree | One giant script |
| 3. Sample data | contacts.csv, reminders.csv | Simulate real users safely | Validated CSVs | Using real people's emails |
| 4. Templates | base.html + one per category | Professional, consistent emails | HTML templates | CSS in `<style>` (Gmail strips it), so styles are inline |
| 5. Scheduling | repeat rules, lead time | Decide *when* to send | Due list | Monthly on the 31st crashes |
| 6. Sending | smtplib, STARTTLS, App Password | Deliver the email | Sent or .eml | Using the normal Gmail password |
| 7. Logging | SQLite with UNIQUE key | Audit trail, no duplicates | delivery_log.db | Sending twice on re-run |
| 8. CLI | run / watch / upcoming / preview / log | Easy daily use | Rich tables | No way to test other dates |
| 9. Dashboard | Streamlit tabs | Manage without code | Control centre | Forgetting to save edits |
| 10. Tests | pytest | Confidence in date logic | 16 tests | Testing only the happy path |
| 11. GitHub | push code, screenshots, sample outputs | Proof of work | Public repo | Committing `.env` |

## 8. Virtual simulation

We don't have a company's mailing list, so the simulation uses:

1. **Contacts**: 10 fictional people in 4 groups (team, students, clients, family), with birthdays. One has an
   invalid email and one is unsubscribed, to test error handling.
2. **Reminders**: 9 realistic reminders: weekly stand-up, monthly bill, one-off deadline, yearly insurance
   renewal, daily medicine, and one paused reminder.
3. **Time travel**: `python main.py run --at "2026-11-23 10:00"` pretends it's a different moment, so a whole
   week can be simulated in seconds. The dashboard has the same date picker.
4. **Dry-run delivery**: emails are written to `outputs/sent_emails/` instead of being sent.
5. **Real delivery (optional)**: put a Gmail App Password in `.env`, then run
   `python main.py test-email you@gmail.com`.

Simulating 21–25 November produced 15 log entries: 14 delivered (dry-run) and 1 skipped (unsubscribed). The
invalid address was rejected at load time, and re-running the same time produced only "duplicate" results.

## 12. Proof-building plan

| Day | Work | Commit message | Screenshot |
|---|---|---|---|
| 1 | Setup, sample contacts & reminders | `chore: project setup with sample contacts and reminders` | Folder structure |
| 2 | HTML templates | `feat: Jinja2 email templates for each reminder type` | Email preview in browser |
| 3 | Scheduler | `feat: repeat rules, lead time and birthday detection` | `python main.py upcoming` |
| 4 | Sending + logging | `feat: SMTP/dry-run mailer with SQLite delivery log` | `python main.py run` output |
| 5 | Dashboard | `feat: Streamlit control centre` | Each dashboard tab |
| 6 | Tests + docs | `docs: README, explanation, interview Q&A` | pytest passing, GitHub page |

## 13. Screenshot checklist

- [ ] Project folder in VS Code
- [ ] `python main.py upcoming` schedule table
- [ ] `python main.py run --at "2026-11-23 09:30"` output
- [ ] An email opened from `outputs/sent_emails/*.html`
- [ ] Dashboard: Schedule, Template studio, Delivery log
- [ ] `outputs/delivery_log.csv` in Excel
- [ ] pytest passing
- [ ] (Optional) a real email received in your Gmail inbox
- [ ] GitHub repository page
