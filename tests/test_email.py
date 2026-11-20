import unittest
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient

from src.scheduler import expand_schedule
from src.mailer import send_email
from src.renderer import render_email
from api.app import app

ROOT = Path(__file__).resolve().parent.parent


class TestEmailAutomation(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_rrule_expansion_daily(self):
        """Verify RFC 5545 daily recurrence expands correctly."""
        dates = expand_schedule("2026-11-20 19:00:00", "FREQ=DAILY;COUNT=3")
        self.assertEqual(len(dates), 3)
        self.assertEqual(dates[0], "2026-11-20 19:00:00")
        self.assertEqual(dates[1], "2026-11-21 19:00:00")
        self.assertEqual(dates[2], "2026-11-22 19:00:00")

    def test_rrule_expansion_weekly(self):
        """Verify weekly recurrence expands properly."""
        dates = expand_schedule("2026-11-20 10:00:00", "FREQ=WEEKLY;COUNT=2")
        self.assertEqual(len(dates), 2)
        self.assertEqual(dates[0], "2026-11-20 10:00:00")
        self.assertEqual(dates[1], "2026-11-27 10:00:00")

    def test_rrule_empty_string_safety(self):
        """Verify empty recurrence string defaults to single occurrence."""
        dates = expand_schedule("2026-11-20 10:00:00", "")
        self.assertEqual(len(dates), 1)
        self.assertEqual(dates[0], "2026-11-20 10:00:00")

    def test_dry_run_mailer(self):
        """Verify dry-run mode returns success without actual transmission."""
        status, err = send_email("user@example.com", "Test Subject", "<p>Hello</p>", dry_run=True)
        self.assertEqual(status, "sent (dry-run)")
        self.assertEqual(err, "")

    def test_invalid_email_handling(self):
        """Verify invalid recipient email format fails gracefully."""
        status, err = send_email("invalid-email-string", "Subject", "<p>Body</p>", dry_run=True)
        self.assertEqual(status, "failed")
        self.assertIn("Invalid email", err)

    def test_template_rendering(self):
        """Verify Jinja2 template personalization and placeholder substitution."""
        templates_dir = ROOT / "templates"
        context = {
            "name": "Priya",
            "title": "Machine Learning Assessment",
            "scheduled_time": "2026-11-25 14:00:00",
            "timezone": "Asia/Kolkata",
        }
        html = render_email(templates_dir, "deadline_reminder.html", context)
        self.assertIn("Priya", html)
        self.assertIn("Machine Learning Assessment", html)

    def test_database_logging(self):
        """Verify messages are correctly inserted and retrievable from SQLite."""
        db_path = ROOT / "db" / "email.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript((ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))
        conn.execute(
            """INSERT INTO message_logs
               (reminder_id, recipient_name, recipient_email, subject, status, error_detail, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("TEST-001", "Test User", "test@example.com", "Test Subject", "sent (dry-run)", "", "2026-11-20 12:00:00"),
        )
        conn.commit()
        row = conn.execute("SELECT recipient_email, status FROM message_logs WHERE reminder_id='TEST-001'").fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "test@example.com")
        self.assertEqual(row[1], "sent (dry-run)")

    def test_api_health(self):
        """Verify FastAPI health status probe."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

    def test_api_logs(self):
        """Verify logs endpoint fetches message records."""
        resp = self.client.get("/logs")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("logs", resp.json())

    def test_api_contacts_and_reminders(self):
        """Verify contact and reminder list endpoints."""
        c_resp = self.client.get("/contacts")
        self.assertEqual(c_resp.status_code, 200)
        self.assertIn("contacts", c_resp.json())

        r_resp = self.client.get("/reminders")
        self.assertEqual(r_resp.status_code, 200)
        self.assertIn("reminders", r_resp.json())

    def test_webhooks_tracking(self):
        """Verify tracking pixel GIF and click-redirect endpoints."""
        open_resp = self.client.get("/t/o/msg123.gif")
        self.assertEqual(open_resp.status_code, 200)
        self.assertEqual(open_resp.headers["content-type"], "image/gif")

        click_resp = self.client.get("/t/c/msg123?url=https://example.com/login", follow_redirects=False)
        self.assertEqual(click_resp.status_code, 307)
        self.assertEqual(click_resp.headers["location"], "https://example.com/login")


if __name__ == "__main__":
    unittest.main()
