import asyncio
import json
from prisma import Prisma

async def main():
    prisma = Prisma()
    await prisma.connect()
    
    # 1. Truncate Emails to keep 20
    emails = await prisma.email.find_many(order={"received_at": "desc"})
    if len(emails) > 20:
        ids_to_delete = [e.id for e in emails[20:]]
        # Delete one by one to ensure safety with prisma python
        for email_id in ids_to_delete:
            await prisma.email.delete(where={"id": email_id})
        print(f"Deleted {len(ids_to_delete)} old emails.")
    else:
        print(f"Only {len(emails)} emails exist. Kept all.")
        
    # 2. Clear simulation templates and repopulate
    await prisma.simulationtemplate.delete_many()
    
    with open("mock_emails.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for item in data:
        await prisma.simulationtemplate.create(data={
            "subject": item["subject"],
            "body": item["body"],
            "is_important": item.get("is_important", False),
            "priority": item.get("priority", "LOW"),
            "category": item.get("category", "OTHER"),
            "reason": item.get("reason", "")
        })
    print(f"Seeded {len(data)} templates.")
        
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
