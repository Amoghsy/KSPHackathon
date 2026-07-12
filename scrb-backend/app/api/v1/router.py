"""
app/api/v1/router.py — top-level router for all /api/v1 endpoints.

All v1 endpoints are imported and mounted here.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import accused, auth, cases, chat, conversations, dashboard, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(accused.router, prefix="/accused", tags=["accused"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(
    conversations.router, prefix="/conversations", tags=["conversations"]
)
