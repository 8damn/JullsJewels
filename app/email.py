"""
E-mailové notifikace přes Gmail SMTP (aiosmtplib).
Voláno z BackgroundTasks — selhání nerozbije response zákazníkovi.
"""
import logging

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


async def _send(to: str, subject: str, body_html: str) -> None:
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP not configured — e-mail not sent: %s", subject)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        logger.info("E-mail odeslán: %s → %s", subject, to)
    except Exception as exc:
        logger.error("E-mail se nepodařilo odeslat: %s", exc)


async def send_order_confirmation(order_id: int, to: str, var_symbol: str, total: float) -> None:
    subject = f"Potvrzení objednávky #{order_id} — Jullsjewels"
    body = f"""
    <h2>Děkujeme za vaši objednávku!</h2>
    <p>Objednávka číslo <strong>#{order_id}</strong> byla přijata.</p>
    <hr>
    <p><strong>K úhradě:</strong> {total:.2f} CZK</p>
    <p><strong>Variabilní symbol:</strong> {var_symbol}</p>
    <p>Po přijetí platby vás budeme informovat e-mailem.</p>
    <br>
    <p>Jullsjewels</p>
    """
    await _send(to, subject, body)


async def send_order_shipped(order_id: int, to: str) -> None:
    subject = f"Vaše objednávka #{order_id} byla odeslána — Jullsjewels"
    body = f"""
    <h2>Dobrá zpráva!</h2>
    <p>Vaše objednávka <strong>#{order_id}</strong> byla odeslána.</p>
    <p>Jullsjewels</p>
    """
    await _send(to, subject, body)
