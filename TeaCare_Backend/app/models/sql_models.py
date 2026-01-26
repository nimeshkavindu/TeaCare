from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
from app.core.database import Base

# --- USER MANAGEMENT ---
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    phone_number = Column(String, unique=True, nullable=True)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String)
    role = Column(String)  # Farmer, Researcher, Expert, Admin
    is_active = Column(Boolean, default=True)
    last_login = Column(String, nullable=True)
    
    # OTP & Verification
    otp_code = Column(String, nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    is_verified = Column(Boolean, default=False)

# --- DISEASE RECOGNITION ---
class DiseaseReport(Base):
    __tablename__ = "disease_reports"

    report_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    disease_name = Column(String)
    confidence = Column(String)
    image_url = Column(String)
    timestamp = Column(String)
    
    # Location Data
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Feedback & Expert Review
    is_correct = Column(String, default="Unknown") 
    user_correction = Column(String, nullable=True)
    verification_status = Column(String, default="Pending") 
    expert_correction = Column(String, nullable=True)    

    # Relationships
    recommendations = relationship("ExpertRecommendation", back_populates="report", cascade="all, delete-orphan")

class ExpertRecommendation(Base):
    __tablename__ = "expert_recommendations"

    recommendation_id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("disease_reports.report_id"))
    expert_id = Column(Integer, ForeignKey("users.user_id")) 
    expert_name = Column(String)
    suggested_disease = Column(String)
    notes = Column(String) 
    timestamp = Column(String)

    report = relationship("DiseaseReport", back_populates="recommendations")

# --- KNOWLEDGE BASE (DISEASES & TREATMENTS) ---
class DiseaseInfo(Base):
    __tablename__ = "diseases"

    disease_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    symptoms = Column(ARRAY(String))
    causes = Column(ARRAY(String))
    
    treatments = relationship("Treatment", back_populates="disease", cascade="all, delete-orphan")

class Treatment(Base):
    __tablename__ = "treatments"

    treatment_id = Column(Integer, primary_key=True, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.disease_id"))
    type = Column(String)        # "Organic" or "Chemical"
    title = Column(String)       
    instruction = Column(String) 
    safety_tip = Column(String)  
    
    disease = relationship("DiseaseInfo", back_populates="treatments")

class KnowledgeBase(Base):
    """
    For Researcher Submissions (New Pathogens)
    """
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)            # Common Name
    scientific_name = Column(String) # Scientific Name
    description = Column(String)
    symptoms = Column(String)
    prevention = Column(String)
    treatment = Column(String)
    image_url = Column(String)       
    status = Column(String, default="Pending") # Pending, Approved, Rejected
    submitted_by = Column(String)    
    timestamp = Column(DateTime, default=datetime.now)

# --- COMMUNITY FORUM ---
class ForumPost(Base):
    __tablename__ = "forum_posts"

    post_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    author_name = Column(String)
    author_role = Column(String, default="Farmer") 
    title = Column(String)
    content = Column(String)
    category = Column(String, default="General")   
    image_url = Column(String, nullable=True)
    timestamp = Column(String)
    
    # Metrics
    score = Column(Integer, default=0) 
    views = Column(Integer, default=0) 
    comment_count = Column(Integer, default=0)

class ForumComment(Base):
    __tablename__ = "forum_comments"

    comment_id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer)
    user_id = Column(Integer)
    author_name = Column(String)
    content = Column(String)
    timestamp = Column(String)

class PostVote(Base):
    __tablename__ = "post_votes"

    vote_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    post_id = Column(Integer)
    vote_type = Column(Integer) # 1 (Up), -1 (Down)

class PostReport(Base):
    __tablename__ = "post_reports"

    report_id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer) 
    user_id = Column(Integer) 
    reason = Column(String)  
    timestamp = Column(String)

# --- SYSTEM & UTILITIES ---
class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String)  # INFO, WARNING, ERROR, SUCCESS
    message = Column(String)
    source = Column(String) 
    timestamp = Column(DateTime, default=datetime.now)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer) # 0 = Global Announcement
    title = Column(String)
    message = Column(String)
    type = Column(String)     # Alert, Info, Success, Announcement
    is_read = Column(Boolean, default=False)
    timestamp = Column(String)