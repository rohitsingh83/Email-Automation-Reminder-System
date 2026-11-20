"""SMTP mailer with safe dry-run simulation mode and error handling."""

import smtplib
from email.message import EmailMessage
from typing import Tuple


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    dry_run: bool = True,
    smtp_host: str = "",
    smtp_port: int = 587,
    smtp_user: str = "",
    smtp_pass: str = "",
) -> Tuple[str, str]:
    if "@" not in to_email:
        return "failed", "Invalid email address"

    if dry_run:
        return "sent (dry-run)", ""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.set_content("Please view this message in an HTML-capable email client.")
    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return "sent", ""
    except Exception as exc:
        return "failed", str(exc)
