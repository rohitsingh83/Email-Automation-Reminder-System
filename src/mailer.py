"""
Send emails.

SmtpMailer   real sending through any SMTP server (Gmail, Outlook, Zoho...)
             using STARTTLS (port 587) or SSL (port 465), with retries.
DryRunMailer safe practice mode: writes each email to outputs/sent_emails/
             as an .eml file (opens in Outlook/Thunderbird) and an .html preview.
"""

import re
import smtplib
import ssl
import time
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path

from .config import OUTPUT_DIR, SmtpSettings
from .renderer import RenderedEmail


def build_message(email: RenderedEmail, to_name: str, to_addr: str, sender_name: str, sender_addr: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = email.subject
    msg["From"] = formataddr((sender_name, sender_addr))
    msg["To"] = formataddr((to_name, to_addr))
    msg["Message-ID"] = make_msgid(domain=sender_addr.split("@")[-1] or "localhost")
    msg.set_content(email.text)                      # plain-text part
    msg.add_alternative(email.html, subtype="html")  # HTML part
    return msg


class DryRunMailer:
    mode = "dry-run"

    def __init__(self, settings: SmtpSettings, folder: Path = OUTPUT_DIR / "sent_emails"):
        self.settings, self.folder = settings, folder
        self.folder.mkdir(parents=True, exist_ok=True)

    def send(self, email: RenderedEmail, to_name: str, to_addr: str, tag: str) -> str:
        msg = build_message(email, to_name, to_addr, self.settings.sender_name,
                            self.settings.user or "reminder-bot@example.com")
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{tag}_{to_addr}")
        (self.folder / f"{safe}.eml").write_bytes(bytes(msg))
        (self.folder / f"{safe}.html").write_text(email.html, encoding="utf-8")
        return f"saved {safe}.eml"


class SmtpMailer:
    mode = "smtp"

    def __init__(self, settings: SmtpSettings, retries: int = 3):
        if not settings.configured:
            raise ValueError("SMTP_USER and SMTP_PASSWORD are not set. Copy .env.example to .env first.")
        self.settings, self.retries = settings, retries

    def _connect(self) -> smtplib.SMTP:
        s = self.settings
        context = ssl.create_default_context()
        if s.port == 465:
            server = smtplib.SMTP_SSL(s.host, s.port, context=context, timeout=30)
        else:
            server = smtplib.SMTP(s.host, s.port, timeout=30)
            server.starttls(context=context)
        server.login(s.user, s.password)
        return server

    def send(self, email: RenderedEmail, to_name: str, to_addr: str, tag: str) -> str:
        msg = build_message(email, to_name, to_addr, self.settings.sender_name, self.settings.user)
        last_error = None
        for attempt in range(1, self.retries + 1):
            try:
                with self._connect() as server:
                    server.send_message(msg)
                return f"sent via {self.settings.host}"
            except smtplib.SMTPAuthenticationError as exc:
                raise RuntimeError("Login failed: check SMTP_USER / SMTP_PASSWORD (use an App Password)") from exc
            except (smtplib.SMTPException, OSError) as exc:   # network hiccup: wait and retry
                last_error = exc
                time.sleep(2 ** attempt)
        raise RuntimeError(f"Failed after {self.retries} attempts: {last_error}")


def get_mailer(settings: SmtpSettings, force_dry_run: bool | None = None):
    dry = settings.dry_run if force_dry_run is None else force_dry_run
    return DryRunMailer(settings) if dry else SmtpMailer(settings)
