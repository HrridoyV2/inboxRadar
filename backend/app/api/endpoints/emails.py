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
    process_and_save_email, get_simulation_templates
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
    Simulates an email scenario by sending it via SMTP and immediately processing it into the DB.
    """
    try:
        sender = f"Simulation Ingest <{settings.EMAIL_USER}>"

        # Send a real SMTP/Cloud email containing the template data
        success, detail_msg = send_email_to_self(payload.subject, payload.body)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Email Delivery Failed: {detail_msg}"
            )

        timestamp = int(time.time())
        rand_id = random.randint(1000, 9999)
        unique_msg_id = f"simulated-{timestamp}-{rand_id}"
        received_at = datetime.datetime.now(datetime.timezone.utc)

        email_record = await process_and_save_email(
            message_id=unique_msg_id,
            sender=sender,
            subject=payload.subject,
            body=payload.body,
            received_at=received_at
        )

        if not email_record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process and save simulated email. The database might be offline."
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
    Sends a test email to the connected email user inbox and immediately processes it.
    """
    success, detail_msg = send_email_to_self(payload.subject, payload.body)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail_msg
        )
        
    timestamp = int(time.time())
    rand_id = random.randint(1000, 9999)
    unique_msg_id = f"test-{timestamp}-{rand_id}"
    received_at = datetime.datetime.now(datetime.timezone.utc)
    
    sender = f"Sandbox Test <{settings.SMTP_SENDER_EMAIL}>"
    await process_and_save_email(
        message_id=unique_msg_id,
        sender=sender,
        subject=payload.subject,
        body=payload.body,
        received_at=received_at
    )
            
    return {"status": "success", "message": detail_msg}


@router.post("/trigger-scan")
async def trigger_scan(_token: dict = Depends(verify_jwt_token)):
    """
    Dummy endpoint since IMAP polling is disabled. Returns success.
    """
    return {
        "status": "success",
        "mode": "LOCAL_SYNC",
        "processed_new_emails": 0
    }


@router.get("/mock-dataset")
async def get_mock_dataset(_token: dict = Depends(verify_jwt_token)):
    """Returns the mock emails dataset for the frontend dropdown."""
    return await get_simulation_templates()
