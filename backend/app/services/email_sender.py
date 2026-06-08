import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory queue for custom mock emails created via the dashboard (Trigger 2) in Mock Mode.
# The poller worker will check this list and process these custom emails immediately.
pending_mock_emails = []

def send_email_to_self(subject: str, body: str) -> tuple[bool, str]:
    """
    Sends an email using SMTP to the configured EMAIL_USER.
    In Mock Mode, it appends to the in-memory queue for processing.
    """
    if settings.MOCK_MODE:
        logger.info(f"[MOCK SMTP] Queueing custom mock email for local simulation: Subject: '{subject}'")
        pending_mock_emails.append({
            "sender": f"Simulator <{settings.SMTP_SENDER_EMAIL}>",
            "subject": subject,
            "body": body
        })
        return True, "Email simulated locally (Mock Mode)."

    # Use SMTP settings from environment
    smtp_server = settings.SMTP_SERVER
    smtp_port = settings.SMTP_PORT
    
    sender_email = settings.SMTP_SENDER_EMAIL
    receiver_email = settings.EMAIL_USER
    password = settings.SMTP_SENDER_PASS

    logger.info(f"Attempting to send real SMTP email via {smtp_server}:{smtp_port}...")

    if not sender_email or not password:
        err_msg = "SMTP Configuration missing: SMTP_SENDER_EMAIL and SMTP_SENDER_PASS must be configured in environment variables."
        logger.error(err_msg)
        return False, err_msg

    message = MIMEMultipart()
    message["From"] = f"InboxRadar Agent <{sender_email}>"
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        # Connect to server and send
        # If using port 465, we use SMTP_SSL. Otherwise, we use STARTTLS on 587.
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=20)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=20)
            server.starttls()  # Secure the connection
            
        server.set_debuglevel(1) # Enable debug output in logs
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        logger.info(f"Successfully sent real SMTP email to {receiver_email} with subject: '{subject}'")
        return True, "Real email sent successfully via SMTP."
    except smtplib.SMTPAuthenticationError:
        err_msg = "SMTP Authentication failed. Check your email/password or use an App Password if using Gmail."
        logger.error(err_msg)
        return False, err_msg
    except Exception as e:
        err_msg = f"SMTP Error ({type(e).__name__}): {str(e)}"
        logger.error(f"Failed to send SMTP email: {err_msg}")
        # Hint for common cloud issues
        if "timed out" in err_msg.lower() or "connection refused" in err_msg.lower():
            logger.warning("HINT: Port 587 might be blocked by your hosting provider (Render). Ensure you have no firewall restrictions.")
        return False, err_msg
