"""
Ticket Management API Endpoints.
CRUD operations, live ML triage upon creation, and ticket conversation replies.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.schemas import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    ReplyCreate,
    ReplyResponse
)
from app.database import (
    create_ticket,
    get_tickets,
    get_ticket_by_id,
    update_ticket,
    delete_ticket,
    add_reply,
    get_replies
)
from app.api.ml import run_ml_pipeline

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

@router.get("", response_model=List[TicketResponse])
def list_tickets(
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    status: Optional[str] = Query(None, description="Filter by status"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    search: Optional[str] = Query(None, description="Search keyword in subject or body"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Retrieve list of support tickets with optional filtering and search."""
    return get_tickets(
        category=category,
        priority=priority,
        status=status,
        sentiment=sentiment,
        search=search,
        limit=limit,
        offset=offset
    )

@router.post("", response_model=TicketResponse, status_code=201)
def submit_ticket(payload: TicketCreate):
    """
    Submit a new support ticket.
    Automatically runs ML triage:
    - Predicts category via TF-IDF + Logistic Regression
    - Measures sentiment via VADER
    - Predicts priority via Random Forest
    """
    full_text = f"{payload.subject}\n{payload.description}"
    ml_result = run_ml_pipeline(full_text, payload.category)

    assigned_cat = payload.category or ml_result["category"]
    assigned_prio = payload.priority or ml_result["priority"]

    ticket = create_ticket(
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        subject=payload.subject,
        description=payload.description,
        category=assigned_cat,
        predicted_category=ml_result["category"],
        category_confidence=ml_result["category_confidence"],
        sentiment_label=ml_result["sentiment_label"],
        sentiment_score=ml_result["sentiment_score"],
        priority=assigned_prio,
        predicted_priority=ml_result["priority"],
        status="Open",
        assigned_agent=payload.assigned_agent or "Unassigned"
    )

    return ticket

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int):
    """Fetch details of a single ticket."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket

@router.put("/{ticket_id}", response_model=TicketResponse)
def modify_ticket(ticket_id: int, payload: TicketUpdate):
    """Update ticket attributes (status, priority, assigned agent, notes, etc.)."""
    ticket = update_ticket(
        ticket_id=ticket_id,
        status=payload.status,
        priority=payload.priority,
        category=payload.category,
        assigned_agent=payload.assigned_agent,
        ai_summary=payload.ai_summary,
        resolution_notes=payload.resolution_notes
    )
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket

@router.delete("/{ticket_id}")
def remove_ticket(ticket_id: int):
    """Delete a ticket."""
    success = delete_ticket(ticket_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return {"status": "Ticket deleted successfully", "id": ticket_id}

@router.get("/{ticket_id}/replies", response_model=List[ReplyResponse])
def list_replies(ticket_id: int):
    """Get conversation message thread for a ticket."""
    return get_replies(ticket_id)

@router.post("/{ticket_id}/replies", response_model=ReplyResponse, status_code=201)
def post_reply(ticket_id: int, payload: ReplyCreate):
    """Post an agent, customer, or AI response to a ticket thread."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    return add_reply(
        ticket_id=ticket_id,
        sender_type=payload.sender_type,
        sender_name=payload.sender_name,
        message=payload.message
    )
