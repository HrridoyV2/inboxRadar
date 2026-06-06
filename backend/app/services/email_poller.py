import os
import json
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import datetime
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import EmailModel
from app.services.ai import classify_email

logger = logging.getLogger(__name__)

# Global list of connected WebSocket managers to notify
websocket_manager = None

# Global event loop reference captured on startup to support threadsafe WS broadcast from background worker threads
main_event_loop = None

def get_mock_emails() -> List[Dict[str, Any]]:
    """Loads mock emails from the JSON file. Supports local and Docker paths."""
    paths_to_try = [
        # Local execution path (4 levels up from backend/app/services)
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "mock_emails.json"),
        # Docker compose run path (3 levels up from app/services inside /app)
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mock_emails.json"),
        # Root directory fallback
        "mock_emails.json"
    ]
    
    path = None
    for p in paths_to_try:
        if os.path.exists(p):
            path = p
            break
            
    if not path:
        logger.error(f"mock_emails.json not found in searched locations: {paths_to_try}")
        return [
            {
                "id": "fallback-offline",
                "sender": "monitoring@tqtech.ie",
                "subject": "CRITICAL: DB Offline",
                "body": "Database is unreachable.",
                "expected_category": "SERVER_DOWN",
                "expected_priority": "HIGH"
            }
        ]

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load mock_emails.json from {path}: {e}")
        return []


def decode_mime_words(s: str) -> str:
    """Decodes email header fields that might be encoded (e.g. UTF-8)."""
    if not s:
        return ""
    try:
        parts = decode_header(s)
        decoded_parts = []
        for word, encoding in parts:
            if isinstance(word, bytes):
                decoded_parts.append(word.decode(encoding or "utf-8", errors="replace"))
            else:
                decoded_parts.append(str(word))
        return "".join(decoded_parts)
    except Exception as e:
        logger.warning(f"Error decoding mime header: {e}")
        return s


def parse_email_body(msg: email.message.Message) -> str:
    """Extracts text body from a MIME email message."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    body += payload.decode(charset, errors="replace")
                except Exception as e:
                    logger.error(f"Error decoding body part: {e}")
    else:
        try:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")
        except Exception as e:
            logger.error(f"Error decoding single part body: {e}")
    
    return body.strip()


def process_and_save_email(
    db: Session,
    message_id: str,
    sender: str,
    subject: str,
    body: str,
    received_at: datetime.datetime
) -> Optional[EmailModel]:
    """
    Checks if email has already been processed. If not, processes with AI
    and saves to database. Returns the database model if saved, or None.
    """
    # 1. Check for duplicates
    existing = db.query(EmailModel).filter(EmailModel.message_id == message_id).first()
    if existing:
        logger.info(f"Email with message_id {message_id} already processed. Skipping.")
        return None

    # 2. Classify with AI (Gemini or Fallback)
    classification = classify_email(sender, subject, body)
    
    # 3. Create database record
    db_email = EmailModel(
        message_id=message_id,
        sender=sender,
        subject=subject,
        body=body,
        received_at=received_at,
        is_important=classification.get("important", False),
        priority=classification.get("priority", "LOW"),
        category=classification.get("category", "OTHER"),
        reason=classification.get("reason", "No reason provided.")
    )
    
    try:
        db.add(db_email)
        db.commit()
        db.refresh(db_email)
        logger.info(f"Processed email: {subject} | Category: {db_email.category} | Important: {db_email.is_important}")
    except Exception as e:
        db.rollback()
        logger.error(f"Database error saving email {message_id}: {e}")
        return None

    # 4. Broadcast via WebSocket if WebSocket manager is available (run in main event loop)
    if websocket_manager and main_event_loop:
        try:
            asyncio.run_coroutine_threadsafe(
                websocket_manager.broadcast_new_email(db_email),
                main_event_loop
            )
        except Exception as ws_err:
            logger.warning(f"Failed to broadcast new email {message_id} via WebSocket: {ws_err}")
            
    return db_email


def poll_imap_inbox() -> int:
    """
    Connects to the IMAP server and checks for new emails.
    Returns the count of new emails successfully processed.
    """
    if not settings.EMAIL_USER or not settings.EMAIL_PASS:
        logger.error("IMAP poller failed: EMAIL_USER and EMAIL_PASS must be configured.")
        return 0

    processed_count = 0
    db = SessionLocal()
    
    try:
        logger.info(f"Connecting to IMAP server: {settings.IMAP_SERVER}...")
        mail = imaplib.IMAP4_SSL(settings.IMAP_SERVER, timeout=15)
        mail.login(settings.EMAIL_USER, settings.EMAIL_PASS)
        mail.select("INBOX")

        # Search for all messages. In production we might search for UNSEEN
        # but to ensure we grab everything, let's search for recent messages.
        # Let's search UNSEEN to prevent parsing huge amounts of history.
        status, response = mail.search(None, "UNSEEN")
        if status != "OK":
            logger.error("IMAP search failed.")
            return 0

        mail_ids = response[0].split()
        logger.info(f"Found {len(mail_ids)} unread emails.")

        for m_id in mail_ids:
            # Fetch message headers and structure
            status, msg_data = mail.fetch(m_id, "(RFC822)")
            if status != "OK":
                logger.error(f"Failed to fetch mail ID {m_id}")
                continue

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Get message ID
                    msg_id = msg.get("Message-ID")
                    if not msg_id:
                        # Fallback unique ID using sender + subject + date
                        msg_id = f"fallback-{hash(msg.get('From', '') + msg.get('Subject', '') + msg.get('Date', ''))}"
                    
                    # Clean message-id
                    msg_id = msg_id.strip("<>")

                    # Check duplicate
                    existing = db.query(EmailModel).filter(EmailModel.message_id == msg_id).first()
                    if existing:
                        continue

                    # Extract details
                    sender = decode_mime_words(msg.get("From"))
                    subject = decode_mime_words(msg.get("Subject"))
                    
                    # Parse date
                    date_str = msg.get("Date")
                    received_at = datetime.datetime.now(datetime.timezone.utc)
                    if date_str:
                        try:
                            received_at = parsedate_to_datetime(date_str)
                        except Exception as e:
                            logger.warning(f"Failed to parse email date: {e}")

                    # Extract body
                    body = parse_email_body(msg)

                    # Process and save
                    result = process_and_save_email(
                        db=db,
                        message_id=msg_id,
                        sender=sender,
                        subject=subject,
                        body=body,
                        received_at=received_at
                    )
                    if result:
                        processed_count += 1
                        
                        # Mark email as read / flag
                        # For testing, we might want to keep it unread or mark it read.
                        # Usually IMAP fetch (RFC822) marks it read automatically.
                        
        mail.close()
        mail.logout()
    except Exception as e:
        logger.error(f"IMAP polling error: {e}")
    finally:
        db.close()
        
    return processed_count


def poll_mock_emails() -> int:
    """
    Simulates receiving emails in mock mode.
    First checks if there are any custom user-submitted emails in the SMTP queue,
    then falls back to parsing mock_emails.json templates.
    """
    logger.info("Polling mock emails...")
    db = SessionLocal()
    processed_count = 0

    try:
        # 1. Process custom user-submitted emails from SMTP Test form
        import app.services.email_sender as email_sender
        if email_sender.pending_mock_emails:
            import random
            custom_email = email_sender.pending_mock_emails.pop(0)
            logger.info(f"Processing custom mock email from queue: Subject: '{custom_email['subject']}'")
            
            timestamp = int(time.time())
            unique_msg_id = f"custom-mock-{timestamp}-{random.randint(1000, 9999)}"
            received_at = datetime.datetime.now(datetime.timezone.utc)
            
            result = process_and_save_email(
                db=db,
                message_id=unique_msg_id,
                sender=custom_email["sender"],
                subject=custom_email["subject"],
                body=custom_email["body"],
                received_at=received_at
            )
            if result:
                processed_count += 1
            return processed_count

        # 2. Fall back to standard mock dataset templates
        mock_data = get_mock_emails()
        if not mock_data:
            return 0

        # Check which mock emails are already processed
        for item in mock_data:
            mock_id = item["id"]
            # Check if this exact mock ID exists in the database
            existing = db.query(EmailModel).filter(EmailModel.message_id == mock_id).first()
            if not existing:
                # Process this mock email
                received_at = datetime.datetime.now(datetime.timezone.utc)
                result = process_and_save_email(
                    db=db,
                    message_id=mock_id,
                    sender=item["sender"],
                    subject=item["subject"],
                    body=item["body"],
                    received_at=received_at
                )
                if result:
                    processed_count += 1
                # Only process one per interval to simulate staggered arrival
                return processed_count

        # 3. If all have been processed, simulate a new random one arriving now
        # by generating a unique timestamped message_id
        import random
        selected = random.choice(mock_data)
        timestamp = int(time.time())
        new_msg_id = f"{selected['id']}-{timestamp}"
        received_at = datetime.datetime.now(datetime.timezone.utc)
        
        result = process_and_save_email(
            db=db,
            message_id=new_msg_id,
            sender=selected["sender"],
            subject=f"[NEW] {selected['subject']}",
            body=selected["body"],
            received_at=received_at
        )
        if result:
            processed_count += 1

    except Exception as e:
        logger.error(f"Mock polling error: {e}")
    finally:
        db.close()

    return processed_count


async def poller_loop():
    """
    Infinite background loop that runs the polling service.
    Default interval is 2 minutes (120 seconds).
    """
    # Sleep initially to let the server start up and DB migrate
    await asyncio.sleep(5)
    
    interval = 120  # 2 minutes
    logger.info("Background Email Poller starting...")
    
    while True:
        try:
            if settings.MOCK_MODE:
                await asyncio.get_event_loop().run_in_executor(None, poll_mock_emails)
            else:
                await asyncio.get_event_loop().run_in_executor(None, poll_imap_inbox)
        except Exception as e:
            logger.error(f"Error in poller worker loop: {e}")
            
        await asyncio.sleep(interval)
