"""
Generative AI API Endpoints.
Provides ticket summarization and AI-assisted response generation.
"""

from fastapi import APIRouter, HTTPException
from app.schemas import (
    AISummarizeRequest,
    AISummarizeResponse,
    AIGenerateReplyRequest,
    AIGenerateReplyResponse
)
from app.genai.engine import GenAIEngine
from app.database import update_ticket, get_ticket_by_id

router = APIRouter(prefix="/api/genai", tags=["Generative AI"])
genai_engine = GenAIEngine()

@router.post("/summarize", response_model=AISummarizeResponse)
def summarize_ticket(payload: AISummarizeRequest):
    """
    Generate an executive 3-point summary of the customer ticket.
    Optionally saves the summary directly to the ticket if ticket_id is supplied.
    """
    result = genai_engine.summarize_ticket(
        subject=payload.subject,
        description=payload.description,
        category=payload.category,
        sentiment_label=payload.sentiment_label,
        priority=payload.priority
    )

    if payload.ticket_id:
        update_ticket(payload.ticket_id, ai_summary=result["summary"])

    return result

@router.post("/generate-reply", response_model=AIGenerateReplyResponse)
def generate_reply(payload: AIGenerateReplyRequest):
    """
    Generate an AI-assisted customer response tailored to tone and issue context.
    """
    result = genai_engine.generate_response(
        subject=payload.subject,
        description=payload.description,
        category=payload.category,
        customer_name=payload.customer_name,
        tone=payload.tone,
        ai_summary=payload.ai_summary
    )
    return result
