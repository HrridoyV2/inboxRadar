import os
import asyncio
import imaplib
import email
from email.header import decode_header
import re
import uuid
from dotenv import load_dotenv

# Load env vars
load_dotenv(r"c:\Projects\InboxRadar2\backend\.env")

from prisma import Prisma

def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                return part.get_payload(decode=True).decode('utf-8', errors='ignore')
    else:
        return msg.get_payload(decode=True).decode('utf-8', errors='ignore')

async def main():
    EMAIL = os.getenv("EMAIL_USER")
    PASS = os.getenv("EMAIL_PASS")
    SERVER = os.getenv("IMAP_SERVER")

    print(f"Connecting to {SERVER} as {EMAIL}...")
    mail = imaplib.IMAP4_SSL(SERVER)
    mail.login(EMAIL, PASS)
    mail.select("inbox")

    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()
    # Get last 15 emails
    latest_ids = email_ids[-15:]

    emails_data = []
    for e_id in latest_ids:
        res, msg_data = mail.fetch(e_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")
                
                sender_header = msg.get("From", "Unknown Sender")
                sender_val, s_encoding = decode_header(sender_header)[0]
                if isinstance(sender_val, bytes):
                    sender_val = sender_val.decode(s_encoding if s_encoding else "utf-8", errors="ignore")
                
                body = get_body(msg)
                if not body:
                    body = "No text content"
                
                # clean up body slightly
                body = body[:2000] # truncate
                
                emails_data.append({
                    "subject": subject or "No Subject",
                    "sender": sender_val,
                    "body": body
                })

    mail.logout()
    print(f"Fetched {len(emails_data)} emails from IMAP.")

    print("Connecting to Prisma...")
    prisma = Prisma()
    await prisma.connect()

    print("Inserting into SimulationTemplate...")
    for data in emails_data:
        try:
            await prisma.simulationtemplate.create(data={
                "id": str(uuid.uuid4()),
                "subject": data["subject"],
                "sender": data["sender"],
                "body": data["body"]
            })
        except Exception as e:
            # Maybe sender isn't actually required on DB side but is on client, or vice versa
            print(f"Error inserting: {e}")

    await prisma.disconnect()
    print("Done! Inserted into database.")

if __name__ == "__main__":
    asyncio.run(main())
