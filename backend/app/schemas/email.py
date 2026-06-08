from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class EmailBase(BaseModel):
    sender: str
    subject: Optional[str] = None
    body: Optional[str] = None
    received_at: Optional[datetime] = None

class EmailCreate(EmailBase):
    message_id: str
    is_important: bool = False
    priority: Optional[str] = "LOW"
    category: Optional[str] = "OTHER"
    reason: Optional[str] = None

class EmailResponse(EmailBase):
    id: UUID
    message_id: str
    is_important: bool
    priority: Optional[str] = None
    category: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class EmailSimulate(BaseModel):
    sender: str
    subject: str
    body: str

class EmailSendTest(BaseModel):
    subject: str
    body: str

class EmailStats(BaseModel):
    total_processed: int
    important_count: int
    unimportant_count: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
