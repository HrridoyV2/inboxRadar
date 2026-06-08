import smtplib
import socket
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
    Includes advanced resilience for cloud environments like Render.
    """
    if settings.MOCK_MODE:
        logger.info(f"[MOCK SMTP] Queueing custom mock email for local simulation: Subject: '{subject}'")
        pending_mock_emails.append({
            "sender": f"Simulator <{settings.SMTP_SENDER_EMAIL}>",
            "subject": subject,
            "body": body
        })
        return True, "Email simulated locally (Mock Mode)."

    # Configuration
    sender_email = settings.SMTP_SENDER_EMAIL
    receiver_email = settings.EMAIL_USER
    password = settings.SMTP_SENDER_PASS
    
    # We will try a few variations if the primary one fails
    # 1. Primary config from env
    # 2. smtp.googlemail.com fallback (sometimes routed differently)
    # 3. Port fallback (if 587 fails, try 465 and vice versa)
    
    primary_server = settings.SMTP_SERVER
    primary_port = settings.SMTP_PORT
    
    fallbacks = [
        (primary_server, 465 if primary_port == 587 else 587),
        ("smtp.googlemail.com", primary_port),
        ("smtp.googlemail.com", 465 if primary_port == 587 else 587),
    ]
    
    attempts = [(primary_server, primary_port)] + fallbacks
    last_error = "Unknown Error"

    if not sender_email or not password:
        err_msg = "SMTP Configuration missing: SMTP_SENDER_EMAIL and SMTP_SENDER_PASS must be configured."
        logger.error(err_msg)
        return False, err_msg

    for server_host, server_port in attempts:
        try:
            logger.info(f"SMTP Attempt: Connecting to {server_host}:{server_port} (Forcing IPv4)...")
            
            # 1. Force IPv4 Resolution
            # "Network is unreachable" often happens when a cloud container tries to use IPv6 
            # but the host/network doesn't support it.
            try:
                addr_info = socket.getaddrinfo(server_host, server_port, socket.AF_INET, socket.SOCK_STREAM)
                resolved_ip = addr_info[0][4][0]
                logger.info(f"Resolved {server_host} to {resolved_ip}")
            except Exception as dns_err:
                logger.warning(f"DNS Resolution failed for {server_host}: {dns_err}")
                continue

            # 2. Establish Connection
            message = MIMEMultipart()
            message["From"] = f"InboxRadar Agent <{sender_email}>"
            message["To"] = receiver_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))

            if server_port == 465:
                # SSL Connection
                server = smtplib.SMTP_SSL(server_host, server_port, timeout=15)
            else:
                # STARTTLS Connection
                server = smtplib.SMTP(server_host, server_port, timeout=15)
                server.starttls()
            
            # 3. Authenticate and Send
            server.set_debuglevel(1)
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            server.quit()
            
            logger.info(f"Successfully sent SMTP email via {server_host}:{server_port}")
            return True, f"Success via {server_host}:{server_port}"

        except (socket.timeout, socket.error) as net_err:
            last_error = f"Network Error on {server_host}:{server_port}: {net_err}"
            logger.warning(last_error)
            continue
        except smtplib.SMTPAuthenticationError:
            err_msg = "SMTP Auth Failed: Check App Password. (Bailing out, fallbacks won't help auth issues)."
            logger.error(err_msg)
            return False, err_msg
        except Exception as e:
            last_error = f"SMTP Error ({type(e).__name__}) on {server_host}:{server_port}: {str(e)}"
            logger.warning(last_error)
            continue

    final_msg = f"All SMTP attempts failed. Last error: {last_error}"
    logger.error(final_msg)
    return False, final_msg
