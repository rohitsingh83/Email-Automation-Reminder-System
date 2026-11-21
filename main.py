"""End-to-end Email Automation & Reminder System (Dry-Run Simulation Mode)."""

import logging
import sqlite3
from datetime import datetime
import pandas as pd

from src.config import settings
from src.renderer import render_email
from src.scheduler import expand_schedule
from src.mailer import send_email

logging.basicConfig(
    filename=str(settings.log_file_path),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logging.getLogger("matplotlib").setLevel(logging.WARNING)  # hide matplotlib INFO noise
logger = logging.getLogger("email_automation")


def main() -> None:
    dry_run = settings.dry_run
    logger.info("Starting Email Automation Dispatch (dry_run=%s)", dry_run)

    contacts = pd.read_csv(settings.contacts_path)
    reminders = pd.read_csv(settings.reminders_path)

    conn = sqlite3.connect(str(settings.db_path))
    try:
        conn.executescript(settings.schema_path.read_text(encoding="utf-8"))

        report_rows = []
        db_insert_rows = []

        for _, rem in reminders.iterrows():
            occurrences = expand_schedule(str(rem["scheduled_time"]), str(rem["rrule"]), max_occurrences=settings.max_occurrences)
            for occ in occurrences:
                for _, contact in contacts.iterrows():
                    if str(contact["unsubscribed"]).lower() == "true":
                        status, err = "skipped (unsubscribed)", "Contact opted out"
                    else:
                        html = render_email(
                            settings.templates_dir,
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
                    db_insert_rows.append(
                        (rem["reminder_id"], contact["name"], contact["email"], f"Reminder: {rem['title']}", status, err, ts)
                    )
                    logger.info("Dispatched %s to %s -> %s", rem["reminder_id"], contact["email"], status)
                    report_rows.append({
                        "reminder_id": rem["reminder_id"],
                        "recipient": contact["name"],
                        "email": contact["email"],
                        "scheduled_for": occ,
                        "status": status,
                    })

        # Batch insert into database
        conn.executemany(
            """INSERT INTO message_logs
               (reminder_id, recipient_name, recipient_email, subject, status, error_detail, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            db_insert_rows,
        )
        conn.commit()
    finally:
        conn.close()

    out_df = pd.DataFrame(report_rows)
    out_csv = settings.outputs_dir / "email_dispatch_report.csv"
    out_df.to_csv(out_csv, index=False)

    print(f"=== Email Automation & Reminder System (dry_run={dry_run}) ===")
    print(out_df.to_string(index=False))
    print(f"\nSaved dispatch report to: {out_csv}")


if __name__ == "__main__":
    main()
