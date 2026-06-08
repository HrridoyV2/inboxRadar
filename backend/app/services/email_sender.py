import smtplib
import socket
import httpx
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory queue for custom mock emails
pending_mock_emails = []

def send_email_via_resend(subject: str, body: str) -> tuple[bool, str]:
    """Sends email using the Resend HTTP API (Port 443, never blocked)."""
    try:
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": "InboxRadar <onboarding@resend.dev>", # Default for free keys, or use your domain
            "to": settings.EMAIL_USER,
            "subject": subject,
            "text": body
        }
        
        logger.info(f"Cloud API Attempt: Sending via Resend HTTP API to {settings.EMAIL_USER}...")
        response = httpx.post(url, headers=headers, json=payload, timeout=15)
        
        if response.status_code in [200, 201]:
            logger.info("Successfully sent email via Cloud HTTP API.")
            return True, "Success via Cloud HTTP API."
        else:
            err_detail = response.json().get('message', 'Unknown API Error')
            logger.error(f"Resend API Failed ({response.status_code}): {err_detail}")
            return False, f"Cloud API Error: {err_detail}"
            
    except Exception as e:
        logger.error(f"Resend API exception: {str(e)}")
        return False, f"Cloud API Exception: {str(e)}"

def send_email_to_self(subject: str, body: str) -> tuple[bool, str]:
    """
    Main entry point for sending emails.
    Prioritizes Cloud HTTP API if configured (to bypass firewall), fallbacks to SMTP.
    """
    if settings.MOCK_MODE:
        logger.info(f"[MOCK SMTP] Queueing for local simulation: {subject}")
        pending_mock_emails.append({
            "sender": f"Simulator <{settings.SMTP_SENDER_EMAIL}>",
            "subject": subject,
            "body": body
        })
        return True, "Email simulated locally (Mock Mode)."

    # 1. PRIORITY: Use Cloud HTTP API (Bypass Render Firewall)
    # If RESEND_API_KEY is present, we use this because it's guaranteed to work over Port 443.
    if settings.RESEND_API_KEY:
        success, msg = send_email_via_resend(subject, body)
        if success:
            return True, msg
        logger.warning("Cloud API failed, falling back to SMTP...")

    # 2. FALLBACK: Resilient SMTP
    # This will likely fail on Render Free but works perfectly on Local/VPS.
    sender_email = settings.SMTP_SENDER_EMAIL
    receiver_email = settings.EMAIL_USER
    password = settings.SMTP_SENDER_PASS
    
    primary_server = settings.SMTP_SERVER
    primary_port = settings.SMTP_PORT
    
    attempts = [
        (primary_server, primary_port),
        (primary_server, 465 if primary_port == 587 else 587),
        ("smtp.googlemail.com", 465),
    ]
    
    last_error = "Unknown Error"

    if not sender_email or not password:
        return False, "SMTP Credentials missing."

    for server_host, server_port in attempts:
        try:
            logger.info(f"SMTP Attempt: {server_host}:{server_port}...")
            
            if server_port == 465:
                server = smtplib.SMTP_SSL(server_host, server_port, timeout=15)
            else:
                server = smtplib.SMTP(server_host, server_port, timeout=15)
                server.starttls()
            
            server.login(sender_email, password)
            
            message = MIMEMultipart()
            message["From"] = f"InboxRadar <{sender_email}>"
            message["To"] = receiver_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))
            
            server.sendmail(sender_email, receiver_email, message.as_string())
            server.quit()
            
            return True, f"Success via SMTP ({server_host})"

        except Exception as e:
            last_error = str(e)
            logger.warning(f"SMTP failed on {server_host}:{server_port}: {last_error}")
            continue

    # Final Failure Message
    if "unreachable" in last_error or "timed out" in last_error:
        final_msg = f"FIREWALL BLOCK DETECTED: Render is blocking your SMTP ports. To fix this, add 'RESEND_API_KEY' to your environment variables."
    else:
        final_msg = f"All attempts failed. Last error: {last_error}"
        
    logger.error(final_msg)
    return False, final_msg
