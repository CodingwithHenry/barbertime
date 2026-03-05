import logging
import secrets
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


async def send_code(to: str, code: str, purpose: str) -> None:
    if purpose == "email_verify":
        subject = "BarberTime – E-Mail bestätigen"
        body = (
            f"Dein Bestätigungscode: {code}\n\n"
            f"Gültig für 15 Minuten.\n\n"
            f"---\n"
            f"Your verification code: {code}\n"
            f"Valid for 15 minutes."
        )
    else:
        subject = "BarberTime – Passwort zurücksetzen"
        body = (
            f"Dein Code zum Zurücksetzen: {code}\n\n"
            f"Gültig für 15 Minuten.\n\n"
            f"---\n"
            f"Your password reset code: {code}\n"
            f"Valid for 15 minutes."
        )

    if not settings.SMTP_HOST:
        # Dev fallback — check `docker compose logs backend`
        logger.warning(f"[EMAIL] To: {to} | {subject} | Code: {code}")
        return

    import aiosmtplib

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER or None,
        password=settings.SMTP_PASSWORD or None,
        start_tls=True,
    )
