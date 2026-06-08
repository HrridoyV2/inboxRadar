from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import datetime
import random
import time
import asyncio

from app.db.prisma_client import prisma
from app.core.security import verify_jwt_token
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
async def get_emails(
    important_only: Optional[bool] = None,
    _token: dict = Depends(verify_jwt_token)
):
    """Retrieves all processed emails, optionally filtering by importance."""
    where_clause = {}
    if important_only is not None:
        where_clause["is_important"] = important_only
        
    emails = await prisma.email.find_many(
        where=where_clause,
        order={"received_at": "desc"}
    )
    return emails


@router.get("/stats", response_model=EmailStats)
async def get_stats(_token: dict = Depends(verify_jwt_token)):
    """Computes analytics statistics of the processed emails."""
    total = await prisma.email.count()
    important = await prisma.email.count(where={"is_important": True})
    unimportant = total - important
    
    high = await prisma.email.count(where={"priority": "HIGH"})
    medium = await prisma.email.count(where={"priority": "MEDIUM"})
    low = await prisma.email.count(where={"priority": "LOW"})
    
    return EmailStats(
        total_processed=total,
        important_count=important,
        unimportant_count=unimportant,
        high_priority_count=high,
        medium_priority_count=medium,
        low_priority_count=low
    )


@router.post("/simulate")
async def simulate_email(
    payload: EmailSimulate,
    _token: dict = Depends(verify_jwt_token)
):
    """
    Simulates receiving a mock email scenario.
    In Mock Mode, it processes and saves the email directly.
    In Real Mode, it dispatches it via SMTP so it goes through the real IMAP poller.
    """
    try:
        if not settings.MOCK_MODE:
            # Send a real SMTP email containing the template data
            success, detail_msg = send_email_to_self(payload.subject, payload.body)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"SMTP Deliverability Error: {detail_msg}. (Network is unreachable). Hint: If you are offline or have no SMTP credentials, set MOCK_MODE=true in your .env file to use the built-in simulator."
                )
            return {
                "status": "sent_via_smtp",
                "message": f"Mock scenario email sent to self ({settings.EMAIL_USER}) via SMTP."
            }

        timestamp = int(time.time())
        rand_id = random.randint(1000, 9999)
        unique_msg_id = f"simulated-{timestamp}-{rand_id}"
        received_at = datetime.datetime.now(datetime.timezone.utc)

        email_record = await process_and_save_email(
            message_id=unique_msg_id,
            sender=payload.sender,
            subject=payload.subject,
            body=payload.body,
            received_at=received_at
        )

        if not email_record:
            # This happens if duplicate (unlikely here) or DB error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process and save simulated email. The database might be offline or the message ID is a duplicate."
            )

        return email_record
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in simulate_email: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error during simulation: {str(e)}"
        )


@router.post("/send-test")
async def send_test_email(
    payload: EmailSendTest,
    _token: dict = Depends(verify_jwt_token)
):
    """
    Sends a test email to the connected email user inbox.
    When the poller runs, it will discover and classify this email.
    """
    success, detail_msg = send_email_to_self(payload.subject, payload.body)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMTP Send Failure: {detail_msg}. Hint: Check your internet connection or set MOCK_MODE=true in .env."
        )
        
    # If in Mock Mode, trigger mock polling immediately so that custom emails are processed instantly
    if settings.MOCK_MODE:
        try:
            await poll_mock_emails()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error triggering immediate mock poll in send-test: {e}")
            
    return {"status": "success", "message": f"Test email sent to self ({settings.EMAIL_USER})"}


@router.post("/trigger-scan")
async def trigger_scan(_token: dict = Depends(verify_jwt_token)):
    """
    Forces an immediate scan of the email inbox.
    Checks IMAP server or loads mock data based on settings.MOCK_MODE.
    """
    if settings.MOCK_MODE:
        new_count = await poll_mock_emails()
        mode = "Mock"
    else:
        new_count = await asyncio.get_event_loop().run_in_executor(None, poll_imap_inbox)
        mode = "Real IMAP"
        
    return {
        "status": "success",
        "mode": mode,
        "processed_new_emails": new_count
    }


@router.get("/mock-dataset")
def get_mock_dataset(_token: dict = Depends(verify_jwt_token)):
    """Returns the mock emails dataset for the frontend dropdown."""
    return get_mock_emails()
