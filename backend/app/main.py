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
        
        # Seed Simulation Templates if table is empty
        try:
            template_count = await prisma.simulationtemplate.count()
            if template_count == 0:
                logger.info("Simulation templates table is empty. Attempting to seed from code...")
                
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
                
                for item in TEMPLATES:
                    await prisma.simulationtemplate.create(
                        data={
                            "subject": item.get("subject", "No Subject"),
                            "body": item.get("body", "")
                        }
                    )
                logger.info(f"Successfully seeded {len(TEMPLATES)} templates to Supabase.")
        except Exception as seed_err:
            logger.error(f"Failed to seed templates during startup: {seed_err}")

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
    
    # Background poller loop removed in favor of live SMTP processing
    
    yield
    
    # Shutdown actions
    logger.info("Shutting down InboxRadar Backend...")
    logger.info("Disconnecting Prisma client...")
    try:
        await prisma.disconnect()
        logger.info("Prisma client disconnected successfully.")
    except Exception as e:
        logger.error(f"Error during Prisma client disconnection: {e}")
        
    # No poller task to stop
        
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
if "*" in origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if "*" not in origins else False, # Credentials cannot be used with '*'
    allow_methods=["*"],
    allow_headers=["*"], # Allow all headers
    expose_headers=["*"],
)

# Register routers
app.include_router(api_router)
app.include_router(websocket.router)  # WebSocket is at /ws

@app.get("/")
async def read_root():
    email_count = -1
    if prisma.is_connected():
        try:
            email_count = await prisma.email.count()
        except Exception:
            email_count = -2 # Error during count
            
    # Generate the same pre-shared static JWT Token for the frontend to pick up
    import jwt
    token = jwt.encode({"iss": "inboxradar-frontend"}, settings.JWT_SECRET, algorithm="HS256")
            
    return {
        "status": "online",
        "app": "InboxRadar2 AI Email Reading Agent API",
        "version": "1.0.1",
        "environment": settings.APP_ENV,
        "api_token": token,
        "database_connected": prisma.is_connected(),
        "database_record_count": email_count
    }
