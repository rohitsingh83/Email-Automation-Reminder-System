"""End-to-end Email Automation & Reminder System (Dry-Run Simulation Mode)."""

import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd

from src.renderer import render_email
from src.scheduler import expand_schedule
from src.mailer import send_email

ROOT = Path(__file__).resolve().parent


def main() -> None:
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    logging.basicConfig(
        filename=str(ROOT / "logs" / "automation.log"),
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    contacts = pd.read_csv(ROOT / "data" / "contacts.csv")
    reminders = pd.read_csv(ROOT / "data" / "reminders.csv")

    conn = sqlite3.connect(str(ROOT / "db" / "email.db"))
    conn.executescript((ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))

    report_rows = []
    for _, rem in reminders.iterrows():
        occurrences = expand_schedule(str(rem["scheduled_time"]), str(rem["rrule"]))
        for occ in occurrences:
            for _, contact in contacts.iterrows():
                if str(contact["unsubscribed"]).lower() == "true":
                    status, err = "skipped (unsubscribed)", "Contact opted out"
                else:
                    html = render_email(
                        ROOT / "templates",
                        str(rem["template_name"]),
                        {
                            "name": contact["name"],
                            "title": rem["title"],
                            "scheduled_time": occ,
                            "timezone": contact["timezone"],
                        },
                    )
                    subject = f"Reminder: {rem['title']} ({occ})"
                    status, err = send_email(contact["email"], subject, html, dry_run=dry_run)

                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute(
                    """INSERT INTO message_logs
                       (reminder_id, recipient_name, recipient_email, subject, status, error_detail, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (rem["reminder_id"], contact["name"], contact["email"], f"Reminder: {rem['title']}", status, err, ts),
                )
                logging.info("%s | %s | %s", rem["reminder_id"], contact["email"], status)
                report_rows.append({
                    "reminder_id": rem["reminder_id"],
                    "recipient": contact["name"],
                    "email": contact["email"],
                    "scheduled_for": occ,
                    "status": status,
                })

    conn.commit()
    conn.close()

    out_df = pd.DataFrame(report_rows)
    out_csv = ROOT / "outputs" / "email_dispatch_report.csv"
    out_df.to_csv(out_csv, index=False)

    print(f"=== Email Automation & Reminder System (dry_run={dry_run}) ===")
    print(out_df.to_string(index=False))
    print(f"\nSaved dispatch report to: {out_csv}")


if __name__ == "__main__":
    main()
