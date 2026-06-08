import asyncio
import logging
import sys
import os

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.getcwd())

from app.db.prisma_client import prisma
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMPLATES = [
    {
        "subject": "CRITICAL: Database Cluster 'db-prod-01' is UNREACHABLE",
        "body": "Monitoring Alert: The production database cluster 'db-prod-01' has stopped responding to health checks. Connection pool is exhausted and latency is > 5000ms. Immediate investigation required."
    },
    {
        "subject": "Urgent: Payment Declined for Subscription #INV-8821",
        "body": "Dear Customer, we were unable to process your recent payment for your 'Enterprise' plan. Your account is scheduled for suspension in 24 hours unless billing details are updated."
    },
    {
        "subject": "Client Complaint: 4-hour downtime on Tuesday",
        "body": "Hi, I am very disappointed with the recent downtime. Our operations were paralyzed for hours. We expect a formal RCA and a credit to our account for this SLA breach."
    },
    {
        "subject": "SECURITY ALERT: Unauthorized Login Attempt Detected",
        "body": "We detected a login attempt to your admin account from an unrecognized IP address (192.168.1.1) in a different country. Please verify if this was you or change your password immediately."
    },
    {
        "subject": "Feature Request: Export Analytics to PDF",
        "body": "Hi team, it would be great if we could export the weekly email stats to a PDF report instead of just CSV. Our management team prefers PDF for their weekly review meetings."
    }
]

async def seed_templates():
    logger.info("Connecting to Supabase via Prisma...")
    try:
        await prisma.connect()
        logger.info("Connected successfully.")
        
        for t in TEMPLATES:
            # Check if it exists by subject to avoid duplicates
            existing = await prisma.simulationtemplate.find_first(
                where={"subject": t["subject"]}
            )
            
            if not existing:
                await prisma.simulationtemplate.create(data=t)
                logger.info(f"Created template: {t['subject']}")
            else:
                logger.info(f"Template already exists: {t['subject']}")
                
        logger.info("Seeding process completed.")
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(seed_templates())
