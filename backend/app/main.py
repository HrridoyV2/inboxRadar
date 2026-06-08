import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.prisma_client import prisma
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
    
    # Connect Prisma client
    logger.info("Connecting Prisma client to the database...")
    try:
        await prisma.connect()
        logger.info("Prisma client database connection established.")
    except Exception as e:
        logger.critical(f"Failed to connect Prisma client to the database: {e}")
        logger.critical("Make sure the database service is reachable and DATABASE_URL is correct.")
        
    # Generate and print the pre-shared static JWT Token
    import jwt
    token = jwt.encode({"iss": "inboxradar-frontend"}, settings.JWT_SECRET, algorithm="HS256")
    logger.info("==================================================================")
    logger.info("JWT API SECURITY TOKEN FOR FRONTEND (NEXT_PUBLIC_API_TOKEN):")
    logger.info(f"{token}")
    logger.info("==================================================================")
    
    # Start poller worker in the background
    logger.info("Launching background IMAP/Mock poller service...")
    poller_task = asyncio.create_task(poller_loop())
    
    yield
    
    # Shutdown actions
    logger.info("Shutting down InboxRadar Backend...")
    logger.info("Disconnecting Prisma client...")
    try:
        await prisma.disconnect()
        logger.info("Prisma client disconnected successfully.")
    except Exception as e:
        logger.error(f"Error during Prisma client disconnection: {e}")
        
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

# Centralized Error Handling Middleware exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"success": False, "detail": "Validation error", "details": exc.errors()}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "detail": str(exc) if settings.APP_ENV == "development" else "Internal server error"}
    )

# Configure CORS
origins = [origin.strip() for origin in settings.ALLOWED_CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["*"],
)

# Register routers
app.include_router(api_router, prefix="/api")
app.include_router(websocket.router, prefix="/api")  # WebSocket moved to /api/ws

@app.get("/")
async def read_root():
    email_count = -1
    if prisma.is_connected():
        try:
            email_count = await prisma.email.count()
        except Exception:
            email_count = -2 # Error during count
            
    return {
        "status": "online",
        "app": "InboxRadar2 AI Email Reading Agent API",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "mock_mode": settings.MOCK_MODE,
        "database_connected": prisma.is_connected(),
        "database_record_count": email_count
    }
