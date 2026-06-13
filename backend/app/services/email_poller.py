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
import hashlib
import re
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.db.prisma_client import prisma
from app.services.ai import classify_email

logger = logging.getLogger(__name__)

# Global list of connected WebSocket managers to notify
websocket_manager = None

# Global event loop reference captured on startup
main_event_loop = None


from pathlib import Path

async def get_simulation_templates() -> List[Dict[str, Any]]:
    """Fetches simulation templates from the database."""
    try:
        # 0. Check for DB connection
        if not prisma.is_connected():
            await prisma.connect()

        # Use raw query to bypass any schema mismatch between local prisma client and live DB
        templates = await prisma.query_raw("SELECT * FROM simulation_templates ORDER BY created_at DESC;")
        
        result = []
        for t in templates:
            # Handle different DB column names (e.g. sender vs from)
            sender_val = t.get('from') or t.get('sender') or f"System Simulator <{settings.EMAIL_USER}>"
            result.append({
                "id": str(t.get('id', '')),
                "subject": t.get('subject', 'No Subject'),
                "body": t.get('body', ''),
                "sender": sender_val
            })
            
        return result
    except Exception as e:
        logger.error(f"Failed to fetch simulation templates: {e}")
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


def get_stable_hash(s: str) -> str:
    """Generates a stable MD5 hash for a string to be used as a fallback ID."""
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def parse_email_body(msg: email.message.Message) -> str:
    """Extracts text body from a MIME email message, falling back to HTML if needed."""
    body = ""
    html_body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" in content_disposition:
                continue
                
            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    body += payload.decode(charset, errors="replace")
                except Exception as e:
                    logger.error(f"Error decoding text body part: {e}")
            elif content_type == "text/html":
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    html_body += payload.decode(charset, errors="replace")
                except Exception as e:
                    logger.error(f"Error decoding html body part: {e}")
    else:
        try:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            content_type = msg.get_content_type()
            
            decoded = payload.decode(charset, errors="replace")
            if content_type == "text/html":
                html_body = decoded
            else:
                body = decoded
        except Exception as e:
            logger.error(f"Error decoding single part body: {e}")
    
    # Prefer plain text, but fall back to HTML if plain text is empty
    result = body.strip()
    if not result and html_body:
        # Basic HTML tag stripping for better classification
        result = re.sub(r'<[^>]+>', '', html_body).strip()
        
    return result


async def process_and_save_email(
    message_id: str,
    sender: str,
    subject: str,
    body: str,
    received_at: datetime.datetime
) -> Optional[Any]:
    """
    Checks if email has already been processed using Prisma. If not, processes with AI
    and saves to database. Returns the database model if saved, or None.
    """
    # 0. Check for DB connection
    if not prisma.is_connected():
        logger.warning("Prisma not connected. Attempting immediate connection...")
        try:
            await prisma.connect()
        except Exception as conn_err:
            logger.error(f"Failed to connect to DB during process_and_save: {conn_err}")
            return None

    # 1. Check for duplicates
    try:
        existing = await prisma.email.find_unique(where={"message_id": message_id})
        if existing:
            logger.info(f"Duplicate email {message_id} skipped.")
            return None # Return None for duplicates so they aren't counted as 'new'
    except Exception as e:
        logger.error(f"Database error checking duplicate for {message_id}: {e}")
        return None

    # 2. Classify with AI (Gemini or Fallback)
    try:
        classification = classify_email(sender, subject, body)
    except Exception as e:
        logger.error(f"Classification failure for {subject}: {e}")
        classification = {"important": False, "priority": "LOW", "category": "OTHER", "reason": "System error during classification."}
    
    # 3. Create database record
    try:
        db_email = await prisma.email.create(
            data={
                "message_id": message_id,
                "sender": sender,
                "subject": subject,
                "body": body,
                "received_at": received_at,
                "is_important": classification.get("important", False),
                "priority": classification.get("priority", "LOW"),
                "category": classification.get("category", "OTHER"),
                "reason": classification.get("reason", "No reason provided.")
            }
        )
        logger.info(f"Saved email: {subject} | Category: {db_email.category}")
    except Exception as e:
        logger.error(f"Database error saving email {message_id}: {e}")
        return None

    # 4. Broadcast via WebSocket if WebSocket manager is available
    if websocket_manager:
        if main_event_loop:
            try:
                # Check if we are currently running in the main event loop
                try:
                    current_loop = asyncio.get_running_loop()
                except RuntimeError:
                    current_loop = None

                if current_loop == main_event_loop:
                    # Already in main loop, just schedule it
                    asyncio.create_task(websocket_manager.broadcast_new_email(db_email))
                else:
                    # In a different thread, use threadsafe bridge
                    asyncio.run_coroutine_threadsafe(
                        websocket_manager.broadcast_new_email(db_email),
                        main_event_loop
                    )
            except Exception as ws_err:
                logger.warning(f"Failed to broadcast new email {message_id} via WebSocket: {ws_err}")
        else:
            logger.warning(f"Cannot broadcast email {message_id}: main_event_loop is not set.")
            
    return db_email


# IMAP Polling and Mock polling removed. Emails are now processed locally on send.
