import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import engine, Base
from app.api.router import api_router
from app.api.endpoints import websocket
from app.services.email_poller import poller_loop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("inboxradar")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Starting up InboxRadar Backend...")
    
    # Capture the main running event loop for threadsafe WS broadcasts
    import app.services.email_poller as email_poller
    email_poller.main_event_loop = asyncio.get_running_loop()
    
    # DNS Diagnostics to find Supabase region
    logger.info("Running DNS Diagnostics to determine Supabase region...")
    try:
        import dns.resolver
        import socket
        for host in ["njghabuyptymtjhcvyrt.supabase.co", "db.njghabuyptymtjhcvyrt.supabase.co"]:
            try:
                answers = dns.resolver.resolve(host, 'CNAME')
                for rdata in answers:
                    logger.info(f"DNS DIAGNOSTIC: {host} CNAME is {rdata.target}")
            except Exception as inner_e:
                # Try getting A record IP to see where it resolves
                try:
                    ip_info = socket.getaddrinfo(host, None)
                    logger.info(f"DNS DIAGNOSTIC: {host} resolved IPs: {set(x[4][0] for x in ip_info)}")
                except Exception:
                    logger.warning(f"Could not resolve CNAME for {host}: {inner_e}")
    except Exception as e:
        logger.warning(f"DNS Diagnostic module error: {e}")
    
    # Create DB tables if not present
    logger.info("Verifying database schema...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verification completed.")
    except Exception as e:
        logger.critical(f"Failed to initialize database tables: {e}")
        logger.critical("Make sure the database service is reachable and DATABASE_URL is correct.")
        
    # Start poller worker in the background
    logger.info("Launching background IMAP/Mock poller service...")
    poller_task = asyncio.create_task(poller_loop())
    
    yield
    
    # Shutdown actions
    logger.info("Shutting down InboxRadar Backend...")
    logger.info("Stopping email poller worker...")
    poller_task.cancel()
    try:
        await poller_task
    except asyncio.CancelledError:
        logger.info("Background poller service stopped successfully.")
    except Exception as e:
        logger.error(f"Error during poller service shutdown: {e}")
        
    logger.info("Server shutdown finalized.")


app = FastAPI(
    title="InboxRadar AI Agent API",
    description="Real-time AI Email Categorizer & Notification Agent",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
# In production, we should specify actual origins rather than wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(api_router, prefix="/api")
app.include_router(websocket.router)  # WebSocket registered at root (/ws)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": "InboxRadar2 AI Email Reading Agent API",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "mock_mode": settings.MOCK_MODE
    }
