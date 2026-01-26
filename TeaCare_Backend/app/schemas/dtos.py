from pydantic import BaseModel, Field, validator
from typing import List, Optional
import re

# --- AUTHENTICATION & USERS ---
class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    contact_type: str 
    contact_value: str 
    secret: str        
    role: str

    @validator('contact_value')
    def validate_contact(cls, v, values):
        ctype = values.get('contact_type', '').lower()
        if ctype == 'email':
            # Simple regex for email validation
            if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
                raise ValueError("Invalid email address format")
        elif ctype == 'phone':
            # Regex for phone (digits, +, -, space, 9-15 chars)
            if not re.match(r"^[\d\+\-\s]{9,15}$", v):
                raise ValueError("Invalid phone number format")
        return v

    @validator('secret')
    def validate_secret(cls, v, values):
        ctype = values.get('contact_type', '').lower()
        if ctype == 'phone':
            if not v.isdigit() or len(v) < 4:
                raise ValueError("PIN must be at least 4 digits")
        elif ctype == 'email':
            if len(v) < 6:
                raise ValueError("Password must be at least 6 characters")
        return v

class VerifyRequest(BaseModel):
    contact_value: str
    otp: str

class LoginRequest(BaseModel):
    identifier: str 
    secret: str 

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    secret: Optional[str] = None

class RoleUpdate(BaseModel):
    role: str

class StatusUpdate(BaseModel):
    is_active: bool

# --- DISEASE ANALYSIS ---
class LocationUpdate(BaseModel):
    latitude: float
    longitude: float

class FeedbackRequest(BaseModel):
    is_correct: bool
    correct_disease: Optional[str] = None

class TriageUpdate(BaseModel):
    status: str            # "Verified" or "Corrected"
    expert_correction: Optional[str] = None

# --- EXPERT RECOMMENDATIONS ---
class RecommendationRequest(BaseModel):
    expert_id: int
    expert_name: str
    suggested_disease: str
    notes: str

# --- COMMUNITY FORUM ---
class CommentRequest(BaseModel):
    post_id: int
    user_id: int
    author_name: str
    content: str

class VoteRequest(BaseModel):
    user_id: int
    vote_type: int # 1 (Up), -1 (Down), 0 (Remove Vote)

# --- KNOWLEDGE BASE (DISEASES & TREATMENTS) ---
class TreatmentDTO(BaseModel):
    type: str
    title: str
    instruction: str
    safety_tip: str

class DiseaseRequest(BaseModel):
    name: str
    symptoms: List[str]
    causes: List[str]
    treatments: List[TreatmentDTO]  

class KnowledgeBaseRequest(BaseModel):
    name: str
    scientific_name: str
    description: str
    symptoms: str
    prevention: str
    treatment: str
    submitted_by: str

class LibraryStatusUpdate(BaseModel):
    status: str  # "Approved" or "Rejected"

# --- NOTIFICATIONS & ADMIN ---
class AnnouncementRequest(BaseModel):
    title: str
    message: str