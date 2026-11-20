# Interview Preparation: Email Automation & Reminder System (10 Q&As)

1. **Explain your project (Non-Technical):** It's an automated reminder assistant that personalizes emails for each recipient, sends them on one-off or recurring schedules, skips anyone who unsubscribed, and logs every delivery.
2. **Explain your project (Technical):** It ingests contact and reminder CSVs, expands RFC 5545 `RRULE` recurrences via `dateutil`, renders personalized HTML with Jinja2, dispatches via `smtplib` (with a safe dry-run mode), and logs outcomes to SQLite and CSV.
3. **Why include a dry-run mode?** It lets developers test template rendering, scheduling, and opt-out logic safely without spamming real inboxes.
4. **How do you handle sensitive SMTP credentials?** Credentials are read from environment variables via `.env`, which is excluded in `.gitignore`, while `.env.example` documents required keys.
5. **How are recurring reminders modeled?** Using standard `RRULE` strings (e.g., `FREQ=DAILY;COUNT=2`) parsed by `dateutil.rrule.rrulestr`.
6. **How do you enforce unsubscribe compliance?** Each contact has an `unsubscribed` flag checked before rendering/sending, logging `skipped (unsubscribed)` when true.
7. **How does error handling work during SMTP failures?** `send_email()` wraps TLS/login/send in `try-except`, returning `("failed", str(exc))` so one bad address never crashes the batch.
8. **How do email open/click tracking webhooks work?** A 1x1 transparent GIF endpoint (`/t/o/{id}.gif`) logs opens and a redirect endpoint (`/t/c/{id}`) logs clicks.
9. **Why use Jinja2 instead of string `.format()`?** Jinja2 supports HTML auto-escaping, conditionals, loops, and clean separation of template files from Python logic.
10. **How would you scale this for high-volume sends?** Move to an async queue (Celery/Redis + `aiosmtplib` or SendGrid API) with rate-limiting and bounce-handling webhooks.
