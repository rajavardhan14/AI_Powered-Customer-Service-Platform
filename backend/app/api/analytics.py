"""
Business Analytics and KPI API Endpoints.
Provides executive dashboard metrics, sentiment health index, category distributions,
and agent performance data.
"""

from fastapi import APIRouter
from app.database import get_analytics_metrics

router = APIRouter(prefix="/api/analytics", tags=["Business Analytics"])

@router.get("/dashboard")
def get_dashboard_analytics():
    """
    Returns aggregated KPIs, category breakdown, sentiment analysis distribution,
    priority matrix, and agent performance rankings for the dashboard.
    """
    return get_analytics_metrics()
