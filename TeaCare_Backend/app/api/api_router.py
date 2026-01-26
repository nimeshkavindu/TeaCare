from fastapi import APIRouter
from app.api.endpoints import (
    auth, 
    analysis, 
    forum, 
    weather, 
    admin, 
    notifications, 
    chatbot, 
    system, 
    library
)

api_router = APIRouter()

# --- 1. Authentication ---
# Handles: /register, /login, /verify-otp, /users/{id}
api_router.include_router(auth.router, tags=["Authentication"])

# --- 2. Disease Analysis ---
# Handles: /predict, /predict/advanced, /history, /reports, /api/analytics
api_router.include_router(analysis.router, tags=["Disease Analysis"])

# --- 3. Community Forum ---
# Handles: /posts, /comments, /vote, /posts/{id}/report
api_router.include_router(forum.router, tags=["Community Forum"])

# --- 4. Weather & Risk ---
# Handles: /weather
api_router.include_router(weather.router, tags=["Weather & Risk"])

# --- 5. Administration ---
# Handles: /api/users, /api/admin/reports, /api/admin/stats
api_router.include_router(admin.router, tags=["Administration"])

# --- 6. Notifications ---
# Handles: /notifications
api_router.include_router(notifications.router, tags=["Notifications"])

# --- 7. AI Chatbot (RAG) ---
# Handles: /chat_stream, /upload_book
api_router.include_router(chatbot.router, tags=["AI Assistant"])

# --- 8. System Health & Logs ---
# Handles: /api/health, /api/logs, /api/researcher/stats
api_router.include_router(system.router, tags=["System Health"])

# --- 9. Library & Diseases (NEW) ---
# Handles: /api/diseases, /api/library
api_router.include_router(library.router, tags=["Library"])