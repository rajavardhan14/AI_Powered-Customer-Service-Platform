"""
API routes subpackage.
"""
from .tickets import router as tickets_router
from .ml import router as ml_router
from .genai import router as genai_router
from .analytics import router as analytics_router
from .export import router as export_router

__all__ = ["tickets_router", "ml_router", "genai_router", "analytics_router", "export_router"]
