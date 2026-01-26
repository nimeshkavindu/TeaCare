from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.core.database import Base, engine
from app.core.config import settings
from app.services.ai_service import ai_manager
from app.api.api_router import api_router  # You create this to aggregate all endpoints

# --- LIFESPAN MANAGER (Replaces Startup Events) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize DB
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database Tables Created")
    except Exception as e:
        print(f"❌ DB Init Error: {e}")

    # 2. Load AI Models
    ai_manager.load_models()
    
    yield
    # Cleanup code (if any) goes here

app = FastAPI(lifespan=lifespan)

# --- MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STATIC FILES ---
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# --- ROUTER ---
# Includes: /register, /login, /predict, /weather, /posts, etc.
app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "TeaCare API is Running 🍃"}