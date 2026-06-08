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
    Returns (success, message).
    """
    # 1. MOCK MODE
    if settings.MOCK_MODE:
        logger.info(f"[MOCK] Queueing simulation: {subject}")
        pending_mock_emails.append({
            "sender": f"Simulator <{settings.SMTP_SENDER_EMAIL}>",
            "subject": subject,
            "body": body
        })
        return True, "MOCK MODE: Email simulated locally (not sent to real inbox)."

    # 2. CLOUD HTTP API (Bypass Render Firewall)
    # Check if key exists and is not just a placeholder
    if settings.RESEND_API_KEY and len(settings.RESEND_API_KEY) > 10:
        success, msg = send_email_via_resend(subject, body)
        # If Cloud API is configured, we DO NOT fall back to SMTP 
        # because SMTP is guaranteed to fail on Render.
        if success:
            return True, f"CLOUD API: {msg}"
        else:
            return False, f"CLOUD API ERROR: {msg}. (Check Resend Dashboard)"

    # 3. SMTP FALLBACK (Works on Local/VPS, blocks on Render Free)
    sender_email = settings.SMTP_SENDER_EMAIL
    receiver_email = settings.EMAIL_USER
    password = settings.SMTP_SENDER_PASS
    
    if not sender_email or not password:
        return False, "SMTP Error: Credentials missing in environment variables."

    attempts = [
        (settings.SMTP_SERVER, settings.SMTP_PORT),
        ("smtp.googlemail.com", 465),
    ]
    
    last_error = ""
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
            
            return True, f"SMTP SUCCESS: Sent via {server_host}."

        except Exception as e:
            last_error = str(e)
            logger.warning(f"SMTP failed on {server_host}:{server_port}: {last_error}")
            continue

    return False, f"NETWORK ERROR: All delivery methods failed. Last error: {last_error}. HINT: Render blocks SMTP. Use RESEND_API_KEY for cloud delivery."
