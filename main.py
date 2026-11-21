"""
Email Automation & Reminder System: command-line tool.

    python main.py run                  send everything that is due right now
    python main.py run --at "2026-11-23 10:00"   pretend it is another time (great for testing)
    python main.py watch --every 15     keep running and check every 15 minutes
    python main.py upcoming --days 14   show the schedule for the next 14 days
    python main.py preview R003         save an HTML preview of one reminder
    python main.py log                  export the delivery history to CSV
    python main.py test-email you@example.com   send one test email (uses .env)

DRY_RUN=true in .env (the default) saves emails to outputs/sent_emails/
instead of sending them. Add --send to really send.
"""

import argparse
import time
from datetime import datetime

from rich.console import Console
from rich.table import Table

from src.config import OUTPUT_DIR, SmtpSettings
from src.data_loader import load_contacts, load_reminders, resolve_recipients
from src.engine import run_once
from src.log_store import DeliveryLog
from src.mailer import get_mailer
from src.renderer import render
from src.scheduler import upcoming

console = Console()
STATUS_STYLE = {"sent": "green", "dry-run": "cyan", "skipped": "yellow", "failed": "red", "duplicate": "dim"}


def load_all():
    contacts, p1 = load_contacts()
    reminders, p2 = load_reminders()
    for problem in p1 + p2:
        console.print(f"[yellow]⚠ {problem}[/]")
    return contacts, reminders


def cmd_run(args, settings):
    now = datetime.strptime(args.at, "%Y-%m-%d %H:%M") if args.at else datetime.now()
    contacts, reminders = load_all()
    mailer = get_mailer(settings, force_dry_run=False if args.send else None)
    log = DeliveryLog()
    results = run_once(now, reminders, contacts, mailer, log, settings)
    log.close()

    console.print(f"\n[bold]Run at {now:%d %b %Y %H:%M}[/]  mode: [cyan]{mailer.mode}[/]")
    if not results:
        console.print("Nothing is due right now. Try:  python main.py upcoming")
        return
    table = Table(header_style="bold white on blue")
    for col in ["Reminder", "Title", "Recipient", "Email", "Status", "Detail"]:
        table.add_column(col)
    for r in results:
        table.add_row(r.reminder_id, r.title, r.recipient, r.email,
                      f"[{STATUS_STYLE.get(r.status, 'white')}]{r.status}[/]", r.detail)
    console.print(table)
    if mailer.mode == "dry-run":
        console.print(f"Emails saved in [bold]{(OUTPUT_DIR / 'sent_emails').relative_to(OUTPUT_DIR.parent)}[/] "
                      "(open the .html files in a browser)")


def cmd_watch(args, settings):
    console.print(f"Watching every {args.every} min. Press Ctrl+C to stop.")
    while True:
        cmd_run(argparse.Namespace(at=None, send=args.send), settings)
        time.sleep(args.every * 60)


def cmd_upcoming(args, settings):
    contacts, reminders = load_all()
    start = datetime.strptime(args.start, "%Y-%m-%d").date() if args.start else datetime.now().date()
    table = Table(title=f"Reminders scheduled for the next {args.days} days", header_style="bold white on blue")
    for col in ["Send on", "Event date", "Reminder", "Category", "Repeat", "Recipients"]:
        table.add_column(col)
    for occ in upcoming(reminders, start, args.days):
        r = occ.reminder
        names = ", ".join(c.first_name for c in resolve_recipients(r, contacts))
        table.add_row(f"{occ.send_date:%a %d %b}", f"{occ.due_date:%a %d %b} {r.due:%H:%M}", r.title,
                      r.category, r.repeat, names)
    console.print(table)


def cmd_preview(args, settings):
    contacts, reminders = load_all()
    r = next((x for x in reminders if x.id.lower() == args.reminder_id.lower()), None)
    if not r:
        console.print(f"[red]No reminder with id {args.reminder_id}[/]")
        return
    people = resolve_recipients(r, contacts)
    email = render(r.category, title=r.title, first_name=people[0].first_name if people else "there",
                   due=r.due.date(), due_time=r.due.strftime("%I:%M %p"), days_left=r.remind_before_days,
                   details=r.details, reminder_id=r.id, sender_name=settings.sender_name)
    path = OUTPUT_DIR / f"preview_{r.id}.html"
    path.parent.mkdir(exist_ok=True)
    path.write_text(email.html, encoding="utf-8")
    console.print(f"Subject: [bold]{email.subject}[/]\nPreview saved to {path.relative_to(OUTPUT_DIR.parent)}")


def cmd_log(args, settings):
    log = DeliveryLog()
    df = log.to_dataframe()
    log.close()
    if df.empty:
        console.print("The delivery log is empty.")
        return
    path = OUTPUT_DIR / "delivery_log.csv"
    df.drop(columns=["id"]).to_csv(path, index=False)
    console.print(df.groupby(["category", "status"]).size().unstack(fill_value=0).to_string())
    console.print(f"\n{len(df)} log entries exported to {path.relative_to(OUTPUT_DIR.parent)}")


def cmd_test(args, settings):
    mailer = get_mailer(settings, force_dry_run=False)
    email = render("general", title="Test email from your Reminder System", first_name="there",
                   due=datetime.now().date(), due_time=datetime.now().strftime("%I:%M %p"),
                   details=["If you can read this, SMTP is set up correctly."], sender_name=settings.sender_name)
    console.print(mailer.send(email, "Test", args.to, "test"))


def main():
    parser = argparse.ArgumentParser(description="Email Automation & Reminder System")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("run", help="send reminders that are due now")
    p.add_argument("--at", help='pretend the time is "YYYY-MM-DD HH:MM"')
    p.add_argument("--send", action="store_true", help="really send even if DRY_RUN=true")
    p = sub.add_parser("watch", help="run continuously")
    p.add_argument("--every", type=int, default=15, help="minutes between checks")
    p.add_argument("--send", action="store_true")
    p = sub.add_parser("upcoming", help="show the schedule")
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--start", help="YYYY-MM-DD (default today)")
    p = sub.add_parser("preview", help="save an HTML preview of a reminder")
    p.add_argument("reminder_id")
    sub.add_parser("log", help="export the delivery log to outputs/delivery_log.csv")
    p = sub.add_parser("test-email", help="send one test email through SMTP")
    p.add_argument("to")
    args = parser.parse_args()

    settings = SmtpSettings()
    handlers = {"run": cmd_run, "watch": cmd_watch, "upcoming": cmd_upcoming, "preview": cmd_preview,
                "log": cmd_log, "test-email": cmd_test}
    if args.command is None:
        args = parser.parse_args(["run"])
    handlers[args.command](args, settings)


if __name__ == "__main__":
    main()
