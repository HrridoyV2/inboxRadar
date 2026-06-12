import asyncio
from dotenv import load_dotenv

load_dotenv(r"c:\Projects\InboxRadar2\backend\.env")
from prisma import Prisma

async def main():
    prisma = Prisma()
    await prisma.connect()
    
    print("Checking database directly...")
    try:
        res = await prisma.query_raw("SELECT * FROM simulation_templates LIMIT 1;")
        if res:
            print("Columns in simulation_templates:", list(res[0].keys()))
    except Exception as e:
        print("Raw query error:", e)

    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
