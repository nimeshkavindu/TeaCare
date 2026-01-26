from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.sql_models import Notification

router = APIRouter()

# ==========================================
# NOTIFICATION ENDPOINTS
# ==========================================

@router.get("/notifications/{user_id}")
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    """
    Fetch notifications for a specific user.
    Includes personal alerts AND Global Announcements (where user_id = 0).
    """
    notifs = db.query(Notification).filter(
        or_(Notification.user_id == user_id, Notification.user_id == 0)
    ).order_by(Notification.id.desc()).all()
    
    return notifs

@router.patch("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int, db: Session = Depends(get_db)):
    """
    Mark a specific notification as 'Read'.
    """
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notif.is_read = True
    db.commit()
    
    return {"message": "Marked as read"}

@router.delete("/notifications/{notif_id}")
def delete_notification(notif_id: int, db: Session = Depends(get_db)):
    """
    Allow users to clear/delete a notification.
    """
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notif)
    db.commit()
    
    return {"message": "Notification deleted"}