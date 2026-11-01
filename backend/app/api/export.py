"""
Data Export and Power BI Integration API Endpoints.
Provides direct CSV exports and Power BI-optimized JSON feeds.
"""

import io
import csv
from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse
from app.database import get_tickets, seed_sample_tickets

router = APIRouter(prefix="/api", tags=["Data Export & Power BI"])

@router.get("/export/csv")
def export_tickets_csv():
    """
    Export all tickets in CSV format, ready for immediate import into
    Microsoft Power BI, Excel, or Tableau.
    """
    tickets = get_tickets(limit=1000)

    output = io.StringIO()
    if tickets:
        writer = csv.DictWriter(output, fieldnames=list(tickets[0].keys()))
        writer.writeheader()
        for t in tickets:
            writer.writerow(t)
    else:
        output.write("No tickets available\n")

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=power_bi_support_tickets.csv"}
    )

@router.get("/export/powerbi-json")
def export_powerbi_json():
    """
    Provides a standardized JSON payload designed for Power BI Web REST Connector
    (Power Query / M-Query).
    """
    tickets = get_tickets(limit=1000)
    return {
        "dataset_name": "Customer Support Tickets & Analytics",
        "total_records": len(tickets),
        "data": tickets
    }

@router.post("/seed")
def seed_database():
    """Populate database with sample support tickets and agent conversation history."""
    return seed_sample_tickets()
