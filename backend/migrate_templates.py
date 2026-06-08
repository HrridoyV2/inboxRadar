import asyncio
import json
import logging
from pathlib import Path
from app.db.prisma_client import prisma

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_mock_data():
    await prisma.connect()
    
    mock_file = Path("mock_emails.json")
    if not mock_file.exists():
        logger.error("mock_emails.json not found in root directory.")
        await prisma.disconnect()
        return

    try:
        with open(mock_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        logger.info(f"Found {len(data)} templates in mock_emails.json. Migrating...")
        
        for item in data:
            subject = item.get("subject", "No Subject")
            body = item.get("body", "")
            
            # Check if template already exists to avoid duplicates
            existing = await prisma.simulationtemplate.find_first(
                where={
                    "subject": subject,
                    "body": body
                }
            )
            
            if not existing:
                await prisma.simulationtemplate.create(
                    data={
                        "subject": subject,
                        "body": body
                    }
                )
                logger.info(f"Migrated template: {subject[:30]}...")
            else:
                logger.info(f"Template already exists, skipping: {subject[:30]}...")
                
        logger.info("Migration completed successfully.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(migrate_mock_data())
