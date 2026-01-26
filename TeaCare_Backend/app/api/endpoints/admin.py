from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from datetime import datetime, timedelta
from collections import Counter
import os

from app.core.database import get_db
from app.models.sql_models import (
    User, SystemLog, DiseaseInfo, Treatment, DiseaseReport, 
    ExpertRecommendation, KnowledgeBase, PostReport, ForumPost, 
    ForumComment, Notification
)
from app.schemas.dtos import (
    RoleUpdate, StatusUpdate, DiseaseRequest, TriageUpdate, 
    LibraryStatusUpdate, AnnouncementRequest
)

router = APIRouter()

# --- HELPER: SYSTEM LOGGING ---
def log_event(db: Session, level: str, source: str, message: str):
    try:
        new_log = SystemLog(level=level, source=source, message=message)
        db.add(new_log)
        db.commit()
    except Exception:
        pass

# ==========================================
# 1. USER MANAGEMENT (Path: /api/users)
# ==========================================

@router.get("/api/users")
def get_all_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.user_id.desc()).limit(100).all()

@router.put("/api/users/{user_id}/role")
def update_user_role(user_id: int, role_data: RoleUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    old_role = user.role
    user.role = role_data.role.lower()
    db.commit()
    log_event(db, "WARNING", "User Mgmt", f"Changed User {user_id} role to {user.role}")
    return {"message": "Role updated"}

@router.put("/api/users/{user_id}/status")
def update_user_status(user_id: int, status: StatusUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = status.is_active
    db.commit()
    return {"message": "User status updated"}

@router.delete("/api/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}

# ==========================================
# 2. DISEASE DB MANAGEMENT (Path: /api/admin/diseases)
# ==========================================

@router.post("/api/admin/diseases")
def save_disease_info(data: DiseaseRequest, db: Session = Depends(get_db)):
    disease = db.query(DiseaseInfo).filter(DiseaseInfo.name == data.name).first()
    if not disease:
        disease = DiseaseInfo(name=data.name)
        db.add(disease)
        db.commit()
        db.refresh(disease)

    disease.symptoms = data.symptoms
    disease.causes = data.causes
    
    # Delete old treatments to replace with new ones
    db.query(Treatment).filter(Treatment.disease_id == disease.disease_id).delete()
    
    for t in data.treatments:
        new_t = Treatment(
            disease_id=disease.disease_id, 
            type=t.type, 
            title=t.title, 
            instruction=t.instruction, 
            safety_tip=t.safety_tip
        )
        db.add(new_t)
    
    db.commit()
    return {"message": "Saved successfully"}

@router.delete("/api/admin/diseases/{id}")
def delete_disease_info(id: int, db: Session = Depends(get_db)):
    db.query(DiseaseInfo).filter(DiseaseInfo.disease_id == id).delete()
    db.commit()
    return {"message": "Deleted"}

# ==========================================
# 3. REPORT TRIAGE (Path: /api/admin/reports_triage)
# ==========================================

@router.get("/api/admin/reports_triage")
def get_reports_triage(filter_by: str = "all", db: Session = Depends(get_db)):
    query = db.query(DiseaseReport).options(joinedload(DiseaseReport.recommendations))
    
    if filter_by == "pending":
        query = query.filter(DiseaseReport.verification_status == "Pending")
    elif filter_by == "conflict":
        query = query.filter(DiseaseReport.is_correct == "No")
    elif filter_by == "high_risk":
        query = query.filter(or_(
            DiseaseReport.disease_name == "Blister Blight", 
            DiseaseReport.disease_name == "Tea Mosaic Virus"
        ))
    
    return query.order_by(DiseaseReport.report_id.desc()).limit(100).all()

@router.patch("/api/admin/reports/{report_id}/triage")
def triage_report(report_id: int, data: TriageUpdate, db: Session = Depends(get_db)):
    report = db.query(DiseaseReport).filter(DiseaseReport.report_id == report_id).first()
    if not report: raise HTTPException(status_code=404, detail="Report not found")
    
    report.verification_status = data.status
    report.expert_correction = data.expert_correction
    db.commit()
    log_event(db, "INFO", "Triage", f"Report #{report_id} marked as {data.status}")
    return {"message": "Updated"}

# ==========================================
# 4. FORUM MODERATION (Path: /api/admin/reports)
# ==========================================

@router.get("/api/admin/reports")
def get_reported_posts(db: Session = Depends(get_db)):
    reports = db.query(PostReport).all()
    post_counts = Counter([r.post_id for r in reports])
    
    results = []
    for pid, count in post_counts.items():
        post = db.query(ForumPost).filter(ForumPost.post_id == pid).first()
        if post:
            reasons = db.query(PostReport.reason).filter(PostReport.post_id == pid).limit(3).all()
            results.append({
                "post": post,
                "report_count": count,
                "reasons": [r[0] for r in reasons]
            })
    results.sort(key=lambda x: x['report_count'], reverse=True)
    return results

@router.delete("/api/admin/posts/{post_id}")
def delete_post_admin(post_id: int, db: Session = Depends(get_db)):
    db.query(PostReport).filter(PostReport.post_id == post_id).delete()
    db.query(ForumComment).filter(ForumComment.post_id == post_id).delete()
    db.query(ForumPost).filter(ForumPost.post_id == post_id).delete()
    db.commit()
    return {"message": "Post deleted"}

@router.post("/api/admin/posts/{post_id}/dismiss")
def dismiss_reports(post_id: int, db: Session = Depends(get_db)):
    db.query(PostReport).filter(PostReport.post_id == post_id).delete()
    db.commit()
    return {"message": "Reports cleared"}

# ==========================================
# 5. LIBRARY MANAGEMENT & STATS
# ==========================================

@router.patch("/api/admin/library/{id}/status")
def update_library_status(id: int, data: LibraryStatusUpdate, db: Session = Depends(get_db)):
    entry = db.query(KnowledgeBase).filter(KnowledgeBase.id == id).first()
    if not entry: raise HTTPException(status_code=404, detail="Not found")
    entry.status = data.status
    db.commit()
    return {"message": "Status updated"}

@router.delete("/api/admin/library/{id}")
def delete_library_entry(id: int, db: Session = Depends(get_db)):
    entry = db.query(KnowledgeBase).filter(KnowledgeBase.id == id).first()
    if entry:
        db.delete(entry)
        db.commit()
    return {"message": "Deleted"}

@router.post("/api/admin/announce")
def send_announcement(data: AnnouncementRequest, db: Session = Depends(get_db)):
    new_notif = Notification(
        user_id=0, 
        title=data.title, 
        message=data.message, 
        type="Announcement", 
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    db.add(new_notif)
    db.commit()
    return {"message": "Sent"}

@router.get("/api/admin/stats")
def get_admin_stats(time_range: str = "7d", db: Session = Depends(get_db)):
    # 1. Global Counts (These ALWAYS stay "All Time" for the top cards)
    total_users = db.query(User).count()
    total_reports = db.query(DiseaseReport).count()
    pending_reviews = db.query(DiseaseReport).filter(DiseaseReport.verification_status == "Pending").count()

    role_counts_query = db.query(User.role, func.count(User.user_id)).group_by(User.role).all()
    
    role_breakdown = {r[0].capitalize(): r[1] for r in role_counts_query if r[0]}

    # 2. Determine Cutoff Date
    now = datetime.now()
    if time_range == "7d":
        cutoff_date = now - timedelta(days=7)
        group_by_format = "%Y-%m-%d" # Daily
    elif time_range == "30d":
        cutoff_date = now - timedelta(days=30)
        group_by_format = "%Y-%m-%d" # Daily
    elif time_range == "6m":
        cutoff_date = now - timedelta(days=180)
        group_by_format = "%Y-%m"    # Monthly
    elif time_range == "1y":
        cutoff_date = now - timedelta(days=365)
        group_by_format = "%Y-%m"    # Monthly
    else:
        cutoff_date = now - timedelta(days=7)
        group_by_format = "%Y-%m-%d"

    # 3. Fetch All & Filter in Python
    # (Since timestamp is a String, we fetch all and filter in memory)
    all_reports = db.query(DiseaseReport).all()
    
    filtered_dates = []
    disease_counts = Counter()
    
    # Track accuracy ONLY for the filtered period
    filtered_verified_count = 0
    filtered_correct_count = 0

    for r in all_reports:
        try:
            # Parse timestamp
            r_date = datetime.strptime(r.timestamp, "%Y-%m-%d %H:%M")
            
            # --- APPLY TIME FILTER ---
            if r_date >= cutoff_date:
                # A. For Trends
                date_key = r_date.strftime(group_by_format)
                filtered_dates.append(date_key)
                
                # B. For Distribution
                disease_counts[r.disease_name] += 1
                
                # C. For Accuracy (Only count this report if it's inside the date range)
                if r.is_correct in ["Yes", "No"]:
                    filtered_verified_count += 1
                    if r.is_correct == "Yes":
                        filtered_correct_count += 1

        except Exception:
            continue

    # 4. Finalize Trends
    date_counter = Counter(filtered_dates)
    sorted_keys = sorted(date_counter.keys())
    trend_data = [{"date": k, "reports": date_counter[k]} for k in sorted_keys]

    # 5. Finalize Distribution (Top 5 for THIS PERIOD)
    top_diseases = disease_counts.most_common(5)
    dist_data = [{"name": name, "value": count} for name, count in top_diseases]

    # 6. Finalize Accuracy (For THIS PERIOD)
    accuracy_rate = 0
    if filtered_verified_count > 0:
        accuracy_rate = round((filtered_correct_count / filtered_verified_count) * 100, 1)

    return {
        "total_users": total_users,
        "role_breakdown": role_breakdown,
        "total_reports": total_reports,
        "pending_reviews": pending_reviews,
        "distribution": dist_data,
        "trends": trend_data,
        "ai_accuracy": accuracy_rate,
        "feedback_count": filtered_verified_count
    }
