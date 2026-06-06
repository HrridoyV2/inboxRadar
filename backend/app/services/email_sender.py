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
        logger.info(f"[MOCK SMTP] Queueing custom mock email: Subject: '{subject}'")
        pending_mock_emails.append({
            "sender": "alexnomad142@gmail.com",
            "subject": subject,
            "body": body
        })
        return True, "Mock email queued successfully."

    # Standard Gmail SMTP settings
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    sender_email = settings.EMAIL_USER
    receiver_email = settings.EMAIL_USER
    password = settings.EMAIL_PASS

    if not sender_email or not password:
        err_msg = "SMTP Configuration missing: EMAIL_USER and EMAIL_PASS must be configured."
        logger.error(err_msg)
        return False, err_msg

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        # Connect to server and send
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()  # Secure the connection
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        logger.info(f"Successfully sent SMTP email to self ({receiver_email}) with subject: '{subject}'")
        return True, "Email sent successfully."
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Failed to send SMTP email to self: {err_msg}")
        return False, err_msg
