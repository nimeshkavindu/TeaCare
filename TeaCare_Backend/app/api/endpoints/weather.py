from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import cast, TIMESTAMP
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.sql_models import Notification
from app.services.weather_service import weather_manager

router = APIRouter()

@router.get("/weather")
async def get_weather_alert(
    lat: float = 6.9271, 
    lng: float = 79.8612, 
    user_id: int = 1, 
    db: Session = Depends(get_db)
):
    """
    Fetches real-time weather, calculates agronomy risks, 
    and triggers a 'Daily Briefing' notification if one hasn't been sent recently.
    """
    # 1. Get Data from Service
    weather_data = await weather_manager.get_forecast(lat, lng)
    
    # 2. Smart Notification Logic
    # Check if we sent a briefing in the last 2 minutes (to prevent spam)
    cutoff = datetime.now() - timedelta(minutes=2)
    
    recent_notif = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.title.contains("Briefing"),
        cast(Notification.timestamp, TIMESTAMP) >= cutoff 
    ).first()

    if not recent_notif:
        # Extract alert data from the service response
        primary = weather_data["primary_alert"]
        current_temp = weather_data["temperature"]
        condition = weather_data["condition"]
        
        briefing_msg = f"Current condition is {condition} ({current_temp}°C). {primary['message']}"
        
        # Decide icon color based on risk
        notif_type = "Alert" if primary["risk"] == "High" else "Info"
        
        new_notif = Notification(
            user_id=user_id,
            title="🌤️ Weather Briefing",
            message=briefing_msg,
            type=notif_type,
            is_read=False,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M") # Store as string to match your model
        )
        db.add(new_notif)
        db.commit()
        print(f"✅ Weather Notification Sent to User {user_id}")

    # 3. Return Data to App
    # We remove the 'primary_alert' internal object before sending to frontend if desired, 
    # but keeping it is fine as it doesn't break anything.
    return weather_data