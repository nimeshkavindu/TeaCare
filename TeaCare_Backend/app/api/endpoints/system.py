from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import time
import httpx
from collections import Counter
import numpy as np
from app.core.database import get_db
from app.models.sql_models import DiseaseReport, User, SystemLog
from app.services.ai_service import ai_manager

router = APIRouter()

# --- SYSTEM HEALTH CHECK (With AI Latency) ---
@router.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    start_total = time.time()
    
    # 1. Database Check
    db_start = time.time()
    try:
        db.execute(text("SELECT 1"))
        db_status = "online"
    except Exception:
        db_status = "offline"
    db_latency = round((time.time() - db_start) * 1000)

    # 2. Vision Model Check (Real Inference)
    vision_start = time.time()
    vision_latency = 0
    vision_status = "offline"
    
    # FIX: Check ai_manager directly, not globals()
    if ai_manager.model is not None:
        try:
            # Create a dummy blank image (1, 224, 224, 3)
            dummy_input = np.zeros((1, 224, 224, 3))
            # Run prediction (verbose=0 hides logs)
            ai_manager.model.predict(dummy_input, verbose=0) 
            vision_latency = round((time.time() - vision_start) * 1000)
            vision_status = "online"
        except Exception as e:
            print(f"Vision Check Failed: {e}")
            vision_status = "error"

    # 3. LLM Model Check (Real Inference)
    llm_start = time.time()
    llm_latency = 0
    llm_status = "offline"

    # FIX: Check ai_manager directly
    if ai_manager.llm is not None:
        try:
            # Ask LLM to generate exactly 1 token (very fast)
            ai_manager.llm("ping", max_tokens=1)
            llm_latency = round((time.time() - llm_start) * 1000)
            llm_status = "online"
        except Exception as e:
            print(f"LLM Check Failed: {e}")
            llm_status = "error"

    # 4. External API Checks
    weather_status = "offline"
    weather_lat = 0
    geo_status = "offline"
    geo_lat = 0

    async with httpx.AsyncClient() as client:
        # Weather
        try:
            w_start = time.time()
            await client.get("https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0&current=temperature_2m", timeout=2.0)
            weather_lat = round((time.time() - w_start) * 1000)
            weather_status = "online"
        except: pass

        # Geo
        try:
            g_start = time.time()
            await client.get("https://nominatim.openstreetmap.org/status.php", headers={"User-Agent": "TeaCare/1.0"}, timeout=2.0)
            geo_lat = round((time.time() - g_start) * 1000)
            geo_status = "online"
        except: pass

    total_latency = round((time.time() - start_total) * 1000)

    return {
        "status": "healthy",
        "api_latency": f"{total_latency}ms",
        "services": {
            "database": { "status": db_status, "latency": f"{db_latency}ms" },
            "vision_model": { "status": vision_status, "latency": f"{vision_latency}ms", "model_name": "ConvNeXt Tiny" },
            "llm_model": { "status": llm_status, "latency": f"{llm_latency}ms", "model_name": "Qwen 0.5B" },
            "weather_api": { "status": weather_status, "latency": f"{weather_lat}ms" },
            "geo_api": { "status": geo_status, "latency": f"{geo_lat}ms" },
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/api/researcher/stats")
def get_researcher_stats(db: Session = Depends(get_db)):
    # 1. Dataset Size
    total_samples = db.query(DiseaseReport).count()

    # 2. Pending Workload
    pending_validations = db.query(DiseaseReport).filter(DiseaseReport.verification_status == "Pending").count()

    # 3. Research Metrics
    all_reports = db.query(DiseaseReport).all()
    uncertainty_count = 0
    disease_counts = Counter()

    for r in all_reports:
        disease_counts[r.disease_name] += 1
        try:
            conf_val = float(r.confidence.replace("%", ""))
            if conf_val < 75.0:
                uncertainty_count += 1
        except: continue

    dominant_disease = disease_counts.most_common(1)[0][0] if disease_counts else "None"

    return {
        "total_samples": total_samples,
        "pending_validations": pending_validations,
        "uncertainty_flags": uncertainty_count,
        "dominant_disease": dominant_disease  
    }

@router.get("/api/logs")
def get_system_logs(limit: int = 10, db: Session = Depends(get_db)):
    return db.query(SystemLog).order_by(SystemLog.timestamp.desc()).limit(limit).all()