from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import datetime
import random
import time
import os
import json

from app.db.session import get_db
from app.db.models import EmailModel
from app.schemas.email import (
    EmailResponse, EmailSimulate, EmailSendTest, EmailStats
)
from app.services.email_poller import (
    process_and_save_email, poll_imap_inbox, poll_mock_emails, get_mock_emails
)
from app.services.email_sender import send_email_to_self
from app.core.config import settings

router = APIRouter()

@router.get("", response_model=List[EmailResponse])
def get_emails(
    important_only: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Retrieves all processed emails, optionally filtering by importance."""
    query = db.query(EmailModel)
    if important_only is not None:
        query = query.filter(EmailModel.is_important == important_only)
    return query.order_by(EmailModel.received_at.desc()).all()


@router.get("/stats", response_model=EmailStats)
def get_stats(db: Session = Depends(get_db)):
    """Computes analytics statistics of the processed emails."""
    total = db.query(EmailModel).count()
    important = db.query(EmailModel).filter(EmailModel.is_important == True).count()
    unimportant = total - important
    
    high = db.query(EmailModel).filter(EmailModel.priority == "HIGH").count()
    medium = db.query(EmailModel).filter(EmailModel.priority == "MEDIUM").count()
    low = db.query(EmailModel).filter(EmailModel.priority == "LOW").count()
    
    return EmailStats(
        total_processed=total,
        important_count=important,
        unimportant_count=unimportant,
        high_priority_count=high,
        medium_priority_count=medium,
        low_priority_count=low
    )


@router.post("/simulate")
def simulate_email(payload: EmailSimulate, db: Session = Depends(get_db)):
    """
    Simulates receiving a mock email scenario.
    In Mock Mode, it processes and saves the email directly.
    In Real Mode, it dispatches it via SMTP so it goes through the real IMAP poller.
    """
    if not settings.MOCK_MODE:
        # Send a real SMTP email containing the template data
        success, detail_msg = send_email_to_self(payload.subject, payload.body)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send mock scenario email via SMTP: {detail_msg}"
            )
        return {
            "status": "sent_via_smtp",
            "message": f"Mock scenario email sent to self ({settings.EMAIL_USER}) via SMTP."
        }

    timestamp = int(time.time())
    rand_id = random.randint(1000, 9999)
    unique_msg_id = f"simulated-{timestamp}-{rand_id}"
    received_at = datetime.datetime.now(datetime.timezone.utc)
    
    email_record = process_and_save_email(
        db=db,
        message_id=unique_msg_id,
        sender=payload.sender,
        subject=payload.subject,
        body=payload.body,
        received_at=received_at
    )
    
    if not email_record:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process and save simulated email."
        )
        
    return email_record


@router.post("/send-test")
def send_test_email(payload: EmailSendTest):
    """
    Sends a test email to the connected email user inbox.
    When the poller runs, it will discover and classify this email.
    """
    success, detail_msg = send_email_to_self(payload.subject, payload.body)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email to self: {detail_msg}"
        )
        
    # If in Mock Mode, trigger mock polling immediately so that custom emails are processed instantly
    if settings.MOCK_MODE:
        try:
            poll_mock_emails()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error triggering immediate mock poll in send-test: {e}")
            
    return {"status": "success", "message": f"Test email sent to self ({settings.EMAIL_USER})"}


@router.post("/trigger-scan")
def trigger_scan():
    """
    Forces an immediate scan of the email inbox.
    Checks IMAP server or loads mock data based on settings.MOCK_MODE.
    """
    if settings.MOCK_MODE:
        new_count = poll_mock_emails()
        mode = "Mock"
    else:
        new_count = poll_imap_inbox()
        mode = "Real IMAP"
        
    return {
        "status": "success",
        "mode": mode,
        "processed_new_emails": new_count
    }


@router.get("/mock-dataset")
def get_mock_dataset():
    """Returns the mock emails dataset for the frontend dropdown."""
    return get_mock_emails()
