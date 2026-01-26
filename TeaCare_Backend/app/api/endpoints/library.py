from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.orm import Session, joinedload
import shutil
import os
import uuid

from app.core.database import get_db
from app.models.sql_models import DiseaseInfo, KnowledgeBase, Treatment

router = APIRouter()

# --- DISEASES (Public/Shared - For Mobile App Offline Mode) ---
@router.get("/api/diseases")
def get_all_diseases(db: Session = Depends(get_db)):
    """
    Fetch all diseases and their treatments.
    Used by the mobile app to show the offline encyclopedia.
    """
    return db.query(DiseaseInfo).options(joinedload(DiseaseInfo.treatments)).all()

# --- LIBRARY (Researcher/Knowledge Base) ---

@router.get("/api/library")
def get_library(status: str = "all", db: Session = Depends(get_db)):
    """
    Fetch Knowledge Base entries.
    Farmers see 'Approved' only. Researchers/Admin see 'All'.
    """
    query = db.query(KnowledgeBase)
    if status == "approved":
        query = query.filter(KnowledgeBase.status == "Approved")
    return query.order_by(KnowledgeBase.id.desc()).all()

@router.post("/api/library")
def submit_pathogen(
    name: str = Form(...),
    scientific_name: str = Form(...),
    description: str = Form(...),
    symptoms: str = Form(...),
    prevention: str = Form(...),
    treatment: str = Form(...),
    submitted_by: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Researchers submit new pathogens for approval.
    """
    file_path = None
    if file:
        os.makedirs("uploads", exist_ok=True)
        ext = os.path.splitext(file.filename)[1]
        filename = f"library_{uuid.uuid4()}{ext}"
        file_location = f"uploads/{filename}"
        
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_path = file_location

    new_entry = KnowledgeBase(
        name=name,
        scientific_name=scientific_name,
        description=description,
        symptoms=symptoms,
        prevention=prevention,
        treatment=treatment,
        submitted_by=submitted_by,
        image_url=file_path,
        status="Pending"
    )
    db.add(new_entry)
    db.commit()
    return {"message": "Pathogen submitted for approval"}