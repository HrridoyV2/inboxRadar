from fastapi import APIRouter
from app.api.endpoints import emails

api_router = APIRouter()
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])
