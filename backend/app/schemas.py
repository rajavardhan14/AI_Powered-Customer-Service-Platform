"""
Pydantic Schemas for API Requests and Responses.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field

class TicketCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, example="John Doe")
    customer_email: str = Field(..., example="john.doe@example.com")
    subject: str = Field(..., min_length=4, example="Cannot login to my account")
    description: str = Field(..., min_length=10, example="My 2FA codes are not arriving on my phone.")
    category: Optional[str] = None
    priority: Optional[str] = None
    assigned_agent: Optional[str] = "Unassigned"

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    assigned_agent: Optional[str] = None
    ai_summary: Optional[str] = None
    resolution_notes: Optional[str] = None

class TicketResponse(BaseModel):
    id: int
    ticket_code: str
    customer_name: str
    customer_email: str
    subject: str
    description: str
    category: str
    predicted_category: str
    category_confidence: float
    sentiment_label: str
    sentiment_score: float
    priority: str
    predicted_priority: str
    status: str
    assigned_agent: str
    ai_summary: str
    resolution_notes: str
    created_at: str
    updated_at: str

class ReplyCreate(BaseModel):
    sender_type: str = Field(..., example="Agent")
    sender_name: str = Field(..., example="Alex Morgan")
    message: str = Field(..., min_length=2, example="We are looking into this.")

class ReplyResponse(BaseModel):
    id: int
    ticket_id: int
    sender_type: str
    sender_name: str
    message: str
    created_at: str

class MLPredictRequest(BaseModel):
    text: str = Field(..., min_length=3, example="My payment was charged twice for this month invoice.")
    category: Optional[str] = None

class MLPredictResponse(BaseModel):
    category: str
    category_confidence: float
    category_probabilities: Dict[str, float]
    sentiment_label: str
    sentiment_score: float
    sentiment_details: Dict[str, float]
    priority: str
    priority_confidence: float
    priority_probabilities: Dict[str, float]
    urgency_score: float

class AISummarizeRequest(BaseModel):
    ticket_id: Optional[int] = None
    subject: str
    description: str
    category: Optional[str] = "General Inquiry"
    sentiment_label: Optional[str] = "Neutral"
    priority: Optional[str] = "Medium"

class AISummarizeResponse(BaseModel):
    summary: str
    provider: str
    status: str

class AIGenerateReplyRequest(BaseModel):
    ticket_id: Optional[int] = None
    customer_name: str = "Valued Customer"
    subject: str
    description: str
    category: Optional[str] = "General Inquiry"
    tone: Optional[str] = "Professional & Solution-Oriented"
    ai_summary: Optional[str] = None

class AIGenerateReplyResponse(BaseModel):
    reply: str
    tone: str
    provider: str
    status: str
