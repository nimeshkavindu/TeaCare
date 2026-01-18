from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
from sqlalchemy import create_engine, Column, Integer, String, Float, or_, text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker, Session, relationship, joinedload
from passlib.context import CryptContext
import shutil
import os
import tensorflow as tf
import numpy as np
from PIL import Image, ImageOps
import io
from datetime import datetime
import pickle
import cv2 
import re 
import httpx
from llama_cpp import Llama
from fastapi.responses import StreamingResponse
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from fastembed import TextEmbedding
from pypdf import PdfReader
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
from typing import List, Optional
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import func
from collections import Counter
from datetime import datetime, timedelta
from dateutil.parser import parse
import cv2
from scipy.stats import entropy
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from fastapi.responses import FileResponse

# --- DATABASE CONFIG ---
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin123@localhost/teacare_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- HELPER: SYSTEM LOGGING ---
def log_event(db: Session, level: str, source: str, message: str):
    try:
        new_log = SystemLog(level=level, source=source, message=message)
        db.add(new_log)
        db.commit()
    except Exception as e:
        print(f"Logging failed: {e}")

# --- HELPER: STARTUP LOGGING (Creates its own DB session) ---
def log_startup_event(level: str, source: str, message: str):
    db = SessionLocal()
    try:
        log_event(db, level, source, message)
    except Exception as e:
        print(f"Startup Log Error: {e}")
    finally:
        db.close()

# --- SECURITY ---
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- MODELS ---
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    phone_number = Column(String, unique=True, nullable=True)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String) 
    role = Column(String) 
    is_active = Column(Boolean, default=True)  
    last_login = Column(String, nullable=True) 
    
class DiseaseReport(Base):
    __tablename__ = "disease_reports"
    report_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    disease_name = Column(String)
    confidence = Column(String)
    image_url = Column(String)
    timestamp = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_correct = Column(String, default="Unknown") 
    user_correction = Column(String, nullable=True)
    verification_status = Column(String, default="Pending") 
    expert_correction = Column(String, nullable=True)    

    recommendations = relationship("ExpertRecommendation", back_populates="report", cascade="all, delete-orphan")

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
    score = Column(Integer, default=0) 
    views = Column(Integer, default=0) 
    comment_count = Column(Integer, default=0) 

class PostVote(Base):
    __tablename__ = "post_votes"
    vote_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    post_id = Column(Integer)
    vote_type = Column(Integer) 

class ForumComment(Base):
    __tablename__ = "forum_comments"
    comment_id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer)
    user_id = Column(Integer)
    author_name = Column(String)
    content = Column(String)
    timestamp = Column(String)

class PostReport(Base):
    __tablename__ = "post_reports"
    report_id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer) 
    user_id = Column(Integer) 
    reason = Column(String)  
    timestamp = Column(String)

class DiseaseInfo(Base):
    __tablename__ = "diseases"
    disease_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    symptoms = Column(ARRAY(String))
    causes = Column(ARRAY(String))
    
    treatments = relationship("Treatment", back_populates="disease", cascade="all, delete-orphan")

class ExpertRecommendation(Base):
    __tablename__ = "expert_recommendations"
    recommendation_id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("disease_reports.report_id"))
    expert_id = Column(Integer, ForeignKey("users.user_id")) 
    expert_name = Column(String)
    suggested_disease = Column(String)
    notes = Column(String) 
    timestamp = Column(String)

    # Relationship back to Report
    report = relationship("DiseaseReport", back_populates="recommendations")

# 2. Add Treatment Class (if not already there)
class Treatment(Base):
    __tablename__ = "treatments"
    treatment_id = Column(Integer, primary_key=True, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.disease_id"))
    type = Column(String)        # "Organic" or "Chemical"
    title = Column(String)       
    instruction = Column(String) 
    safety_tip = Column(String)  
    
    disease = relationship("DiseaseInfo", back_populates="treatments")

class SystemLog(Base):
    __tablename__ = "system_logs"
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String)  # "INFO", "WARNING", "ERROR", "SUCCESS"
    message = Column(String)
    source = Column(String) # e.g., "Auth", "AI Engine", "Database"
    timestamp = Column(DateTime, default=datetime.now)
    

class StatusUpdate(BaseModel):
    is_active: bool

class RoleUpdate(BaseModel):
    role: str

# --- INIT DATABASE ---
try:
    Base.metadata.create_all(bind=engine)
    log_startup_event("SUCCESS", "Database", "PostgreSQL Connection Established & Tables Checked")
except Exception as e:
    print(f"DB Init Error: {e}")

# --- VECTOR DATABASE SETUP (Custom FastEmbed Wrapper) ---
print("Initializing Vector Database (FastEmbed Mode)...")

class MyFastEmbedFunction(EmbeddingFunction):
    def __init__(self):
        self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    
    def __call__(self, input: Documents) -> Embeddings:
        return list(self.model.embed(input))

try:
    chroma_client = chromadb.PersistentClient(path="./tea_vectordb")
    knowledge_collection = chroma_client.get_or_create_collection(
        name="tea_knowledge",
        embedding_function=MyFastEmbedFunction()
    )
    print("✅ Vector Database Ready!")
    log_startup_event("SUCCESS", "Knowledge Base", "Vector Database (ChromaDB) Initialized")
except Exception as e:
    print(f"Vector DB Error: {e}")
    log_startup_event("ERROR", "Knowledge Base", f"Vector DB Failed: {str(e)}")


# --- VALIDATION SCHEMAS ---
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
            if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
                raise ValueError("Invalid email address format")
        elif ctype == 'phone':
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

class LoginRequest(BaseModel):
    identifier: str 
    secret: str     

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float

class FeedbackRequest(BaseModel):
    is_correct: bool
    correct_disease: str = None

class CommentRequest(BaseModel):
    post_id: int
    user_id: int
    author_name: str
    content: str


# --- APP SETUP ---
app = FastAPI()
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- HELPER: BLUR CHECK ---
def is_blurry(image_bytes, threshold=35.0):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    score = cv2.Laplacian(img, cv2.CV_64F).var()
    print(f"DEBUG: Blur Score = {score:.2f}") 
    return score < threshold

# --- LOAD AI MODEL ---
print("Loading AI Model...")
model = None  
class_names = []

try:
    model = tf.keras.models.load_model('models/tea_leaf_convnext.keras')
    with open('models/class_names.pkl', 'rb') as f:
        class_names = pickle.load(f)
    print("✅ Model loaded successfully!")
    log_startup_event("SUCCESS", "AI Engine", "ConvNeXt Disease Model Loaded")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    log_startup_event("ERROR", "AI Engine", f"ConvNeXt Model Failed: {str(e)}")
    class_names = ["Error"] * 10


# --- PREDICTION ENDPOINT ---
@app.post("/predict")
async def predict_disease(
    user_id: int = Form(...),
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    
    if model is None:
        log_event(db, "ERROR", "AI Engine", "Prediction failed: Model not loaded")
        return {
            "error": "The AI Model is offline. Check server logs.",
            "disease_name": "System Error", 
            "confidence": "0%"
        }
    try:
        # 1. Read Content
        contents = await file.read()
        
        # 2. Check for Blur
        if is_blurry(contents):
            log_event(db, "WARNING", "AI Engine", f"Rejected image (Blur) from User {user_id}")
            return {
                "error": "Image is too blurry. Please hold the camera steady and try again.",
                "blur_score": "Low"
            }

        # 3. Save File
        ext = os.path.splitext(file.filename)[1]
        file_location = f"uploads/{uuid.uuid4()}{ext}"
        with open(file_location, "wb") as buffer:
            buffer.write(contents)

        # 4. TTA (Test Time Augmentation)
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        image = image.resize((224, 224))
        
        img_orig = np.asarray(image)
        img_rot = np.asarray(image.rotate(90))
        img_flip = np.asarray(ImageOps.mirror(image))

        batch = np.array([img_orig, img_rot, img_flip])

        # 5. Predict
        predictions = model.predict(batch)
        avg_score = np.mean(predictions, axis=0)
        final_score = tf.nn.softmax(avg_score)

        class_idx = np.argmax(final_score)
        disease_name = class_names[class_idx] 
        confidence = float(np.max(final_score)) * 100
        
        # Check if confidence is too low
        if confidence < 50:
            log_event(db, "WARNING", "AI Engine", f"Low Confidence ({confidence:.1f}%) for User {user_id}")
            disease_name = "Unknown / Unclear"
            symptoms = ["The AI is not sure. The image might be unclear, or this disease is not in our database."]
            causes = ["Low image quality", "Unrecognized pattern"]
            treatment_list = []
        else:
            db_disease_name = re.sub(r'^\d+\.\s*', '', disease_name).strip() 
            disease_name = db_disease_name
            # 6. FETCH DYNAMIC DATA
            disease_info = db.query(DiseaseInfo).filter(DiseaseInfo.name.ilike(disease_name)).first()
            
            if disease_info:
                symptoms = disease_info.symptoms
                causes = disease_info.causes
                treatments_db = db.query(Treatment).filter(Treatment.disease_id == disease_info.disease_id).all()
                treatment_list = [{"type": t.type, "title": t.title, "instruction": t.instruction, "safety_tip": t.safety_tip} for t in treatments_db]
            else:
                symptoms = ["Leaf appears healthy"] if "Healthy" in disease_name else ["No details available."]
                causes = []
                treatment_list = []


        initial_status = "Pending"

        # Rule 1: If AI is super sure (>90%) AND it's a common disease, Auto-Verify it.
        if confidence > 85.0 and disease_name != "Unknown / Unclear":
            initial_status = "Auto-Verified"

        # Rule 2: If the result is "Unknown", always force human review
        if disease_name == "Unknown / Unclear":
            initial_status = "Pending"
        
        # 7. Save Report
        new_report = DiseaseReport(
            user_id=user_id,
            disease_name=disease_name,
            confidence=f"{confidence:.1f}%",
            image_url=file_location,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            verification_status=initial_status
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report) 

        # --- LOG SUCCESS ---
        log_event(db, "INFO", "AI Engine", f"Prediction: {disease_name} ({confidence:.1f}%)")
        
        return {
            "report_id": new_report.report_id,
            "disease_name": disease_name,
            "confidence": f"{confidence:.2f}%",
            "symptoms": symptoms,
            "causes": causes,
            "treatments": treatment_list,
            "image_url": file_location
        }

    except Exception as e:
        log_event(db, "ERROR", "AI Engine", f"Prediction Crash: {str(e)}")
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- UPDATE LOCATION ---
@app.patch("/history/{report_id}/location")
def update_location(report_id: int, loc: LocationUpdate, db: Session = Depends(get_db)):
    report = db.query(DiseaseReport).filter(DiseaseReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.latitude = loc.latitude
    report.longitude = loc.longitude
    db.commit()
    # No explicit log needed for location updates to save DB space, 
    # but you could add one if desired.
    return {"message": "Location saved"}

# --- PUBLIC MAP ENDPOINT ---
@app.get("/reports/locations")
def get_public_reports(db: Session = Depends(get_db)):
    reports = db.query(DiseaseReport).filter(DiseaseReport.latitude != None).all()
    return reports

# --- FEEDBACK ---
@app.post("/history/{report_id}/feedback")
def submit_feedback(report_id: int, feedback: FeedbackRequest, db: Session = Depends(get_db)):
    report = db.query(DiseaseReport).filter(DiseaseReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.is_correct = "Yes" if feedback.is_correct else "No"
    
    if not feedback.is_correct:
        report.user_correction = feedback.correct_disease

        report.verification_status = "Pending" 
        log_event(db, "WARNING", "Triage", f"Report #{report_id} FLAGGED by User Feedback (User Disagreed)")
    
    db.commit()
    return {"message": "Feedback received"}

# --- REGISTER ---
@app.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    c_type = user.contact_type.lower()
    c_val = user.contact_value.lower() if c_type == 'email' else user.contact_value

    existing_user = db.query(User).filter(
        or_(User.phone_number == c_val, User.email == c_val)
    ).first()
    
    if existing_user:
        log_event(db, "WARNING", "Auth", f"Register Failed: User already exists ({c_val})")
        raise HTTPException(status_code=400, detail="User already registered")

    new_phone = c_val if c_type == "phone" else None
    new_email = c_val if c_type == "email" else None
    hashed_secret = get_password_hash(user.secret)

    new_user = User(full_name=user.full_name, phone_number=new_phone, email=new_email, password_hash=hashed_secret, role=user.role)
    db.add(new_user)
    db.commit()

    log_event(db, "SUCCESS", "Auth", f"New user registered: {c_val}")
    return {"message": "Registration successful"}

# --- LOGIN ---
@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    ident = request.identifier.lower() if "@" in request.identifier else request.identifier
    user = db.query(User).filter(or_(User.phone_number == ident, User.email == ident)).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # --- 1. CHECK IF BANNED ---
    if not user.is_active:
        log_event(db, "WARNING", "Auth", f"Blocked login attempt by BANNED user: {ident}")
        raise HTTPException(status_code=403, detail="Your account has been suspended. Contact Admin.")

    if not verify_password(request.secret, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # --- 2. UPDATE LAST LOGIN ---
    user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M")
    db.commit()

    log_event(db, "SUCCESS", "Auth", f"User logged in: {user.full_name}")
    return {"message": "Login successful", "user_id": user.user_id, "name": user.full_name, "role": user.role}

@app.get("/history/{user_id}")
def get_history(user_id: int, db: Session = Depends(get_db)):
    return db.query(DiseaseReport).filter(DiseaseReport.user_id == user_id).order_by(DiseaseReport.report_id.desc()).all()

# --- WEATHER ENDPOINT ---
@app.get("/weather")
async def get_weather_alert(lat: float = 6.9271, lng: float = 79.8612, db: Session = Depends(get_db)):
    try:
        # 1. Fetch Weather Data (Open-Meteo)
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
        
        # 1.5 Fetch Location Name (Nominatim Reverse Geocoding) - NEW!
        # We assume the estate is in Sri Lanka, but this works globally.
        geo_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}"
        
        location_name = "Unknown Estate"
        
        async with httpx.AsyncClient() as client:
            # Fetch Weather
            weather_resp = await client.get(weather_url)
            weather_data = weather_resp.json()
            
            # Fetch Location Name
            # User-Agent is required by OpenStreetMap policies
            try:
                geo_resp = await client.get(geo_url, headers={"User-Agent": "TeaCareApp/1.0"})
                if geo_resp.status_code == 200:
                    geo_data = geo_resp.json()
                    address = geo_data.get("address", {})
                    
                    # Try to get the most relevant name (City > Town > Village > State)
                    city = address.get("city") or address.get("town") or address.get("village")
                    state = address.get("state") or address.get("province")
                    
                    if city and state:
                        location_name = f"{city}, {state}"
                    elif city:
                        location_name = city
                    elif state:
                        location_name = state
            except Exception as e:
                print(f"Geocoding Error: {e}")

        # 2. Extract Weather Data
        current = weather_data.get("current", {})
        temp = current.get("temperature_2m", 0)
        humidity = current.get("relative_humidity_2m", 0)
        wind_speed = current.get("wind_speed_10m", 0)
        rain = current.get("precipitation", 0)
        code = current.get("weather_code", 0)

        # 3. Interpret Weather Code
        def get_condition(c):
            if c in [0]: return "Sunny"
            if c in [1, 2, 3]: return "Cloudy"
            if c in [45, 48]: return "Foggy"
            if c in [51, 53, 55, 61, 63, 65, 80, 81, 82]: return "Rainy"
            if c >= 95: return "Storm"
            return "Clear"

        condition = get_condition(code)

        # 4. Calculate Tea Risk
        risk_level = "Low"
        forecast_disease = "None"
        advice = "Conditions are favorable for plantation work."

        if humidity > 85 and condition in ["Rainy", "Cloudy"]:
            risk_level = "High"
            forecast_disease = "Blister Blight"
            advice = "Critical risk! Pause plucking if leaves are wet."
        elif temp > 30 and humidity < 60:
            risk_level = "Medium"
            forecast_disease = "Red Spider Mite"
            advice = "Dry heat detected. Inspect for mites."

        # 5. Spraying Advice
        spraying_condition = "Safe"
        if wind_speed > 20:
            spraying_condition = "Unsafe (Windy)"
        elif rain > 0.5 or condition == "Rainy":
             spraying_condition = "Unsafe (Rain)"

        # 6. Process Daily Forecast
        daily = weather_data.get("daily", {})
        forecast_list = []
        if "time" in daily:
            for i in range(len(daily["time"])):
                forecast_list.append({
                    "date": daily["time"][i],
                    "max_temp": round(daily["temperature_2m_max"][i]),
                    "min_temp": round(daily["temperature_2m_min"][i]),
                    "rain_sum": daily["precipitation_sum"][i],
                    "condition": get_condition(daily["weather_code"][i])
                })

        log_event(db, "INFO", "Weather", f"Risk check at {location_name} (Lat:{lat:.2f})")

        return {
            "location": location_name, 
            "temperature": round(temp),
            "humidity": humidity,
            "wind_speed": wind_speed,
            "condition": condition,
            "risk_level": risk_level,
            "disease_forecast": forecast_disease,
            "advice": advice,
            "spraying_condition": spraying_condition,
            "daily_forecast": forecast_list
        }

    except Exception as e:
        print(f"Weather Error: {e}")
        log_event(db, "ERROR", "Weather", f"Weather API Failed: {str(e)}")
        return {
            "location": "Offline", "temperature": 0, "humidity": 0,
            "condition": "Error", "risk_level": "Unknown", 
            "disease_forecast": "Unknown", "advice": "Check internet connection.",
            "spraying_condition": "Unknown", "daily_forecast": []
        }

# --- COMMUNITY FORUM ENDPOINTS ---
# 1. Create Post (Now with Category & Role)
@app.post("/posts")
def create_post(
    user_id: int = Form(...),
    author_name: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form("General"), # NEW
    file: UploadFile = File(None), 
    db: Session = Depends(get_db)
):
    # 1. Get User Role for Badge
    user = db.query(User).filter(User.user_id == user_id).first()
    role = user.role if user else "Farmer"

    # 2. Handle Image
    image_path = None
    if file:
        ext = os.path.splitext(file.filename)[1]
        file_location = f"uploads/{uuid.uuid4()}{ext}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        image_path = file_location

    # 3. Save
    new_post = ForumPost(
        user_id=user_id,
        author_name=author_name,
        author_role=role,
        title=title,
        content=content,
        category=category,
        image_url=image_path, 
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        score=0,
        views=0,
        comment_count=0
    )
    db.add(new_post)
    db.commit()
    
    log_event(db, "SUCCESS", "Forum", f"New {category} post by {author_name}")
    return {"message": "Post created"}

# 2. Get Posts (With Filters: Popular, Newest, Unanswered, My Posts)
@app.get("/posts")
def get_posts(
    sort: str = "newest",
    filter_by: str = "all",
    search: str = "",
    user_id: int = None,
    db: Session = Depends(get_db)
):
    query = db.query(ForumPost)

    # A. Search
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(ForumPost.title.ilike(search_term), ForumPost.content.ilike(search_term)))

    # B. Filters
    if filter_by == "unanswered":
        # We handle this filter effectively by checking the real count later or doing a join here
        # For simplicity in this fix, let's filter after counting or assume the column will be updated
        pass 
    elif filter_by == "my_posts" and user_id:
        query = query.filter(ForumPost.user_id == user_id)
    elif filter_by == "category_alert":
        query = query.filter(ForumPost.category == "Disease Alert")

    # C. Sorting
    if sort == "popular":
        query = query.order_by(ForumPost.score.desc())
    else:
        query = query.order_by(ForumPost.post_id.desc())

    posts = query.all()
    
    # D. Attach Vote Status AND Real Comment Count
    results = []
    for p in posts:
        user_vote = 0
        if user_id:
            vote_record = db.query(PostVote).filter(PostVote.post_id == p.post_id, PostVote.user_id == user_id).first()
            if vote_record:
                user_vote = vote_record.vote_type
        
        # --- FIX: Count comments directly from the database ---
        real_comment_count = db.query(ForumComment).filter(ForumComment.post_id == p.post_id).count()

        post_dict = p.__dict__.copy()
        if "_sa_instance_state" in post_dict: del post_dict["_sa_instance_state"]
        
        post_dict['user_vote'] = user_vote
        post_dict['comment_count'] = real_comment_count # <--- Forces correct number
        
        # Handle "Unanswered" filter logic manually if needed
        if filter_by == "unanswered" and real_comment_count > 0:
            continue

        results.append(post_dict)

    return results

class VoteRequest(BaseModel):
    user_id: int
    vote_type: int # 1 (Up), -1 (Down), 0 (Remove Vote)

@app.post("/posts/{post_id}/vote")
def vote_post(post_id: int, vote: VoteRequest, db: Session = Depends(get_db)):
    post = db.query(ForumPost).filter(ForumPost.post_id == post_id).first()
    if not post: raise HTTPException(status_code=404, detail="Post not found")

    # Check existing vote
    existing_vote = db.query(PostVote).filter(PostVote.post_id == post_id, PostVote.user_id == vote.user_id).first()

    if existing_vote:
        # If user is changing vote (e.g. Up -> Down)
        # Remove old value from score
        post.score -= existing_vote.vote_type
        
        if vote.vote_type == 0:
            # Removing vote completely
            db.delete(existing_vote)
        else:
            # Updating vote
            existing_vote.vote_type = vote.vote_type
            post.score += vote.vote_type
    else:
        # New Vote
        if vote.vote_type != 0:
            new_vote = PostVote(user_id=vote.user_id, post_id=post_id, vote_type=vote.vote_type)
            db.add(new_vote)
            post.score += vote.vote_type

    db.commit()
    return {"new_score": post.score}

@app.post("/comments")
def create_comment(comment: CommentRequest, db: Session = Depends(get_db)):
    # 1. Create Comment
    new_comment = ForumComment(
        post_id=comment.post_id,
        user_id=comment.user_id,
        author_name=comment.author_name,
        content=comment.content,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    db.add(new_comment)
    
    # 2. Update Post Count
    post = db.query(ForumPost).filter(ForumPost.post_id == comment.post_id).first()
    if post:
        post.comment_count += 1 
        
    db.commit()
    return {"message": "Comment added"}

@app.get("/posts/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db)):
    return db.query(ForumComment).filter(ForumComment.post_id == post_id).all()

# 4. User: Delete Own Post
@app.delete("/posts/{post_id}")
def delete_own_post(post_id: int, user_id: int, db: Session = Depends(get_db)):
    post = db.query(ForumPost).filter(ForumPost.post_id == post_id).first()
    if not post: raise HTTPException(status_code=404, detail="Post not found")

    # Security Check
    if post.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own posts")

    # Cleanup
    db.query(PostVote).filter(PostVote.post_id == post_id).delete()
    db.query(ForumComment).filter(ForumComment.post_id == post_id).delete()
    db.query(PostReport).filter(PostReport.post_id == post_id).delete()
    
    db.delete(post)
    db.commit()
    return {"message": "Post deleted"}

# --- GET SINGLE POST (For Deep Linking) ---
@app.get("/posts/{post_id}")
def get_single_post(post_id: int, user_id: int = None, db: Session = Depends(get_db)):
    post = db.query(ForumPost).filter(ForumPost.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Calculate Vote Status
    user_vote = 0
    if user_id:
        vote_record = db.query(PostVote).filter(PostVote.post_id == post_id, PostVote.user_id == user_id).first()
        if vote_record:
            user_vote = vote_record.vote_type

    # Convert to Dict
    post_dict = post.__dict__.copy()
    if "_sa_instance_state" in post_dict: del post_dict["_sa_instance_state"]
    post_dict['user_vote'] = user_vote
    
    return post_dict

# --- MODERATION ENDPOINTS ---

# 1. User Reports a Post (Mobile App calls this)
@app.post("/posts/{post_id}/report")
def report_post(post_id: int, user_id: int = Form(...), reason: str = Form(...), db: Session = Depends(get_db)):
    # Check if this user already reported this post to prevent spamming
    existing = db.query(PostReport).filter(PostReport.post_id == post_id, PostReport.user_id == user_id).first()
    if existing:
        return {"message": "You have already reported this post."}

    new_report = PostReport(
        post_id=post_id, 
        user_id=user_id, 
        reason=reason, 
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    db.add(new_report)
    db.commit()
    
    log_event(db, "WARNING", "Forum", f"Post {post_id} reported by User {user_id}")
    return {"message": "Report submitted"}

# 2. Admin: Get All Reported Posts
@app.get("/api/admin/reports")
def get_reported_posts(db: Session = Depends(get_db)):
    # Get all reports
    reports = db.query(PostReport).all()
    
    # Group reports by Post ID
    from collections import Counter
    post_counts = Counter([r.post_id for r in reports])
    
    results = []
    for pid, count in post_counts.items():
        post = db.query(ForumPost).filter(ForumPost.post_id == pid).first()
        if post:
            # Get specific reasons for this post (limit to 3 for preview)
            reasons = db.query(PostReport.reason).filter(PostReport.post_id == pid).limit(3).all()
            reason_list = [r[0] for r in reasons]
            
            results.append({
                "post": post,
                "report_count": count,
                "reasons": reason_list
            })
            
    # Sort by number of reports (Highest first)
    results.sort(key=lambda x: x['report_count'], reverse=True)
    return results

# 3. Admin: Delete a Post (and its reports/comments)
@app.delete("/api/admin/posts/{post_id}")
def delete_post_admin(post_id: int, db: Session = Depends(get_db)):
    # Delete related data first (Cascade)
    db.query(PostReport).filter(PostReport.post_id == post_id).delete()
    db.query(ForumComment).filter(ForumComment.post_id == post_id).delete()
    
    # Delete the post
    post = db.query(ForumPost).filter(ForumPost.post_id == post_id).first()
    if post:
        db.delete(post)
        db.commit()
        log_event(db, "WARNING", "Moderation", f"Admin DELETED Post {post_id} due to reports")
        return {"message": "Post deleted"}
    raise HTTPException(status_code=404, detail="Post not found")

# 4. Admin: Ignore/Dismiss Reports (Keep post, clear reports)
@app.post("/api/admin/posts/{post_id}/dismiss")
def dismiss_reports(post_id: int, db: Session = Depends(get_db)):
    db.query(PostReport).filter(PostReport.post_id == post_id).delete()
    db.commit()
    log_event(db, "INFO", "Moderation", f"Reports dismissed for Post {post_id}")
    return {"message": "Reports cleared"}


# --- AI ENGINE ---
print("Loading LLM...")
llm = None
try:
    llm = Llama(
        model_path="models/qwen2.5-0.5b-instruct-q4_k_m.gguf", 
        n_ctx=2048,      
        n_threads=4,     
        verbose=False
    )
    print("LLM is Ready!")
    log_startup_event("SUCCESS", "AI Engine", "Qwen-0.5B LLM Loaded")
except Exception as e:
    print(f"LLM Load Failed: {e}")
    log_startup_event("ERROR", "AI Engine", f"LLM Load Failed: {str(e)}")

# --- CHATBOT LOGIC ---
@app.post("/upload_book")
async def upload_book(file: UploadFile = File(...), category: str = Form("General"), db: Session = Depends(get_db)):
    print(f"📥 Receiving PDF: {file.filename}...")

    try:
        pdf_reader = PdfReader(file.file)
        full_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text: full_text += text + "\n"
        
        chunk_size = 1000
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        
        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{file.filename}_part_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({"source": file.filename, "category": category})

        knowledge_collection.add(ids=ids, documents=documents, metadatas=metadatas)
        
        log_event(db, "SUCCESS", "Knowledge Base", f"Ingested manual: {file.filename} ({len(chunks)} chunks)")
        return {"message": f"Successfully learned {len(chunks)} chunks from '{file.filename}'."}
    except Exception as e:
        log_event(db, "ERROR", "Knowledge Base", f"PDF Ingestion Failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process PDF")
    
def retrieve_context(query: str, db: Session):
    try:
        # A. Query Vector DB (Chroma)
        # We ask for 3 most relevant chunks
        results = knowledge_collection.query(
            query_texts=[query],
            n_results=3 
        )

        context_list = []
        sources_found = []  # List to track filenames

        # B. Process Vector Results
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                # Extract metadata
                meta = results['metadatas'][0][i]
                source = meta.get('source', 'Unknown File')
                
                # Append to context for the AI
                context_list.append(f"Fact: {doc} (Source: {source})")
                
                # Add to our source list for the user display
                sources_found.append(source)
        
        # C. Fallback to SQL Database (DiseaseInfo Table)
        # If vector search was weak or empty, we check our traditional DB
        clean_query = query.replace("?", "").replace(".", "")
        diseases = db.query(DiseaseInfo).filter(DiseaseInfo.name.ilike(f"%{clean_query}%")).limit(1).all()
        
        for d in diseases:
            context_list.append(f"Disease Info: {d.name}. Symptoms: {', '.join(d.symptoms)}.")
            sources_found.append(f"TeaCare Database ({d.name})")

        # D. Handle "No Data" Case
        if not context_list:
            # Log the warning so you know what content is missing
            log_event(db, "WARNING", "RAG Engine", f"No context found for: '{query[:30]}...'")
            return "NO_DATA_FOUND", []

        # E. Log Success
        # Remove duplicates from source list for cleaner logs
        unique_sources = list(set(sources_found))
        source_str = ", ".join(unique_sources)
        log_event(db, "INFO", "RAG Engine", f"Retrieved context from: {source_str}")

        return "\n\n".join(context_list), unique_sources

    except Exception as e:
        print(f"Retrieval Error: {e}")
        log_event(db, "ERROR", "RAG Engine", f"Retrieval Crashed: {str(e)}")
        return "NO_DATA_FOUND", []

@app.post("/chat_stream")
async def chat_stream(
    user_query: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if LLM is loaded to prevent crashes
    if llm is None:
        log_event(db, "ERROR", "Chatbot", "Chat failed: LLM not loaded")
        raise HTTPException(status_code=503, detail="AI Service Unavailable")

    # Step 1: Get Context AND Sources
    context, sources = retrieve_context(user_query, db)
    
    # --- LOGGING (Privacy Safe) ---
    # Log only the first 50 chars to protect user privacy while keeping utility
    safe_log_query = user_query[:50] + "..." if len(user_query) > 50 else user_query
    log_event(db, "INFO", "Chatbot", f"Query: {safe_log_query}")

    # Step 2: Build Strict Prompt
    if context == "NO_DATA_FOUND":
        system_instruction = (
            "You are a Tea Assistant. "
            "The user asked a question, but you have NO information about it in your database. "
            "Politely apologize and say you only know about topics in the uploaded TeaCare documents."
        )
    else:
        system_instruction = (
            "You are an expert Tea Agronomist. "
            "Use the Context below to answer the farmer's question. "
            "STRICT RULE: Answer ONLY using the facts provided in the Context. "
            "If the Context does not contain the answer, say 'I do not have that specific information'. "
            "Keep answers concise."
        )

    prompt = f"""<|im_start|>system
{system_instruction}

Context:
{context}<|im_end|>
<|im_start|>user
{user_query}<|im_end|>
<|im_start|>assistant
"""
    
    # Step 3: Generator Function (Streams response + Sources)
    def iter_tokens():
        # A. Stream the AI's Answer first
        stream = llm(
            prompt, 
            max_tokens=256, 
            stop=["<|im_end|>"], 
            stream=True, 
            temperature=0.5
        )
        
        for output in stream:
            yield output['choices'][0]['text']
        
        # B. Append the Sources at the bottom (if any exist)
        # This runs AFTER the AI finishes talking
        if sources:
            yield "\n\n---\n**Sources:**\n"
            for src in sources:
                yield f"• {src}\n"

    return StreamingResponse(iter_tokens(), media_type="text/markdown")

# --- REPLACE YOUR EXISTING health_check FUNCTION WITH THIS ---
@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    start_total = time.time()
    
    # 1. Check Database
    db_start = time.time()
    try:
        db.execute(text("SELECT 1"))
        db_status = "online"
    except Exception:
        db_status = "offline"
    db_latency = round((time.time() - db_start) * 1000)

    # 2. Check Vision Model (ConvNeXt)
    # Checks if loaded in memory
    vision_status = "online" if 'model' in globals() and model is not None else "offline"
    
    # 3. Check LLM (Qwen)
    # Checks if loaded in memory
    llm_status = "online" if 'llm' in globals() and llm is not None else "offline"

    # 4. Check External APIs (Real Ping)
    weather_status = "offline"
    weather_lat = 0
    geo_status = "offline"
    geo_lat = 0

    async with httpx.AsyncClient() as client:
        # A. Weather API Ping
        try:
            w_start = time.time()
            # Minimal request to Open-Meteo
            await client.get("https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0&current=temperature_2m", timeout=2.0)
            weather_lat = round((time.time() - w_start) * 1000)
            weather_status = "online"
        except Exception:
            weather_status = "offline"

        # B. OpenStreetMap Ping
        try:
            g_start = time.time()
            # Minimal request to Nominatim Status
            await client.get("https://nominatim.openstreetmap.org/status.php", headers={"User-Agent": "TeaCare/1.0"}, timeout=2.0)
            geo_lat = round((time.time() - g_start) * 1000)
            geo_status = "online"
        except Exception:
            geo_status = "offline"

    total_latency = round((time.time() - start_total) * 1000)

    return {
        "status": "healthy",
        "api_latency": f"{total_latency}ms",
        "services": {
            "database": {"status": db_status, "latency": f"{db_latency}ms"},
            "vision_model": {"status": vision_status, "model_name": "ConvNeXt Tiny"},
            "llm_model": {"status": llm_status, "model_name": "Qwen 0.5B"},
            "weather_api": {"status": weather_status, "latency": f"{weather_lat}ms"},
            "geo_api": {"status": geo_status, "latency": f"{geo_lat}ms"},
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/logs")
def get_system_logs(limit: int = 10, db: Session = Depends(get_db)):
    logs = db.query(SystemLog).order_by(SystemLog.timestamp.desc()).limit(limit).all()
    return logs

# --- USER MANAGEMENT ENDPOINTS ---

# 1. Get All Users (for Admin Dashboard)
@app.get("/api/users")
def get_all_users(db: Session = Depends(get_db)):
    # In a real app, add limit/offset for pagination
    users = db.query(User).order_by(User.user_id.desc()).limit(100).all()
    return users

# 2. Update User Role (e.g., Promote Farmer -> Researcher)


@app.put("/api/users/{user_id}/role")
def update_user_role(user_id: int, role_data: RoleUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_role = user.role
    user.role = role_data.role
    db.commit()
    
    log_event(db, "WARNING", "User Mgmt", f"Changed User {user_id} role from {old_role} to {user.role}")
    return {"message": "Role updated"}

# 3. Delete User
@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    log_event(db, "WARNING", "User Mgmt", f"Deleted User ID {user_id} ({user.full_name})")
    return {"message": "User deleted"}


@app.put("/api/users/{user_id}/status")
def update_user_status(user_id: int, status: StatusUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = status.is_active
    db.commit()
    
    action = "Unbanned" if status.is_active else "Banned"
    log_event(db, "WARNING", "User Mgmt", f"{action} User ID {user_id}")
    return {"message": f"User {action}"}

# --- KNOWLEDGE BASE ENDPOINTS (For Arrays) ---

# Pydantic Model (Data Validation)
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


@app.get("/api/diseases")
def get_all_diseases(db: Session = Depends(get_db)):
    # usage of 'joinedload' forces the DB to fetch treatments immediately
    return db.query(DiseaseInfo).options(joinedload(DiseaseInfo.treatments)).all()

@app.post("/api/admin/diseases")
def save_disease_info(data: DiseaseRequest, db: Session = Depends(get_db)):
    # 1. Check if Disease exists
    disease = db.query(DiseaseInfo).filter(DiseaseInfo.name == data.name).first()
    
    if not disease:
        disease = DiseaseInfo(name=data.name)
        db.add(disease)
        db.commit() # Commit to get an ID
        db.refresh(disease)

    # 2. Update Basic Info
    disease.symptoms = data.symptoms
    disease.causes = data.causes
    
    # 3. Update Treatments (Strategy: Delete old, add new)
    # This is the easiest way to ensure we don't have duplicates or stale data
    db.query(Treatment).filter(Treatment.disease_id == disease.disease_id).delete()
    
    for t in data.treatments:
        new_treatment = Treatment(
            disease_id=disease.disease_id,
            type=t.type,
            title=t.title,
            instruction=t.instruction,
            safety_tip=t.safety_tip
        )
        db.add(new_treatment)
    
    db.commit()
    return {"message": "Disease and treatments saved successfully"}

@app.delete("/api/admin/diseases/{id}")
def delete_disease_info(id: int, db: Session = Depends(get_db)):
    # Cascade delete will handle treatments automatically
    db.query(DiseaseInfo).filter(DiseaseInfo.disease_id == id).delete()
    db.commit()
    return {"message": "Deleted"}

# --- ADMIN REPORT TRIAGE ENDPOINTS ---

# 1. Get Reports (With Filters for Triage)
@app.get("/api/admin/reports_triage")
def get_reports_triage(filter_by: str = "all", db: Session = Depends(get_db)):
    # Add .options(joinedload(...)) to fetch recommendations efficiently
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

# 2. Verify or Correct a Report
class TriageUpdate(BaseModel):
    status: str            # "Verified" or "Corrected"
    expert_correction: Optional[str] = None

@app.patch("/api/admin/reports/{report_id}/triage")
def triage_report(report_id: int, data: TriageUpdate, db: Session = Depends(get_db)):
    report = db.query(DiseaseReport).filter(DiseaseReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.verification_status = data.status
    report.expert_correction = data.expert_correction
    db.commit()
    
    # Log it
    log_event(db, "INFO", "Triage", f"Report #{report_id} marked as {data.status}")
    return {"message": "Report status updated"}

# --- EXPERT RECOMMENDATION ENDPOINTS ---

class RecommendationRequest(BaseModel):
    expert_id: int
    expert_name: str
    suggested_disease: str
    notes: str

# 1. Experts: Submit a Recommendation
@app.post("/api/reports/{report_id}/recommend")
def submit_recommendation(report_id: int, rec: RecommendationRequest, db: Session = Depends(get_db)):
    # Verify User is actually an Expert/Researcher
    user = db.query(User).filter(User.user_id == rec.expert_id).first()
    if not user or user.role not in ["Expert", "Researcher", "Admin"]:
        raise HTTPException(status_code=403, detail="Only Experts can submit recommendations")

    new_rec = ExpertRecommendation(
        report_id=report_id,
        expert_id=rec.expert_id,
        expert_name=rec.expert_name,
        suggested_disease=rec.suggested_disease,
        notes=rec.notes,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    db.add(new_rec)
    
    # Optional: Update status to "Under Review" since an expert looked at it
    report = db.query(DiseaseReport).filter(DiseaseReport.report_id == report_id).first()
    if report.verification_status == "Pending":
        report.verification_status = "Under Review"
        
    db.commit()
    return {"message": "Recommendation submitted"}

# 2. Admin: Get Recommendations for a Report
@app.get("/api/reports/{report_id}/recommendations")
def get_recommendations(report_id: int, db: Session = Depends(get_db)):
    return db.query(ExpertRecommendation).filter(ExpertRecommendation.report_id == report_id).all()

# -- Stats --

@app.get("/api/admin/stats")
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

# Add this endpoint to main.py
@app.get("/api/researcher/stats")
def get_researcher_stats(db: Session = Depends(get_db)):
    # 1. Total Samples (Dataset Size)
    total_samples = db.query(DiseaseReport).count()

    # 2. Pending Validations (Workload)
    pending_validations = db.query(DiseaseReport).filter(
        DiseaseReport.verification_status == "Pending"
    ).count()

    # 3. Analyze Reports for Research Metrics
    all_reports = db.query(DiseaseReport).all()
    uncertainty_count = 0
    disease_counts = Counter()

    for r in all_reports:
        # Count disease types
        disease_counts[r.disease_name] += 1

        # Count low confidence (Uncertainty Flags)
        try:
            # Clean string "98.5%" -> 98.5
            conf_val = float(r.confidence.replace("%", ""))
            if conf_val < 75.0:
                uncertainty_count += 1
        except:
            continue

    # 4. Determine Dominant Strain
    dominant_disease = "None"
    if disease_counts:
        # Get the most common disease
        most_common = disease_counts.most_common(1)[0]
        dominant_disease = most_common[0]

    return {
        "total_samples": total_samples,
        "pending_validations": pending_validations,
        "uncertainty_flags": uncertainty_count,
        "dominant_disease": dominant_disease  
    }

# --- HELPER: COMPUTER VISION FORENSICS ---
def analyze_lesions_advanced(image_path):
    try:
        # 1. Load & Preprocess
        img = cv2.imread(image_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. VEGETATION INDEX (Green Leaf Index - GLI)
        # GLI = (2G - R - B) / (2G + R + B)
        # We calculate the mean GLI for the whole leaf
        R, G, B = cv2.split(img_rgb)
        # Avoid division by zero
        denom = (2.0 * G + R + B) + 0.00001
        gli_matrix = (2.0 * G - R - B) / denom
        avg_gli = np.mean(gli_matrix)

        # 3. TEXTURE ANALYSIS (Entropy & Contrast)
        # Entropy = measure of randomness (high for fungal textures)
        # Contrast = measure of local intensity variation
        from skimage.feature import graycomatrix, graycoprops
        # Calculate GLCM (Gray Level Co-occurrence Matrix)
        # We downscale slightly for speed if needed, but 224x224 is fast enough
        glcm = graycomatrix(gray, distances=[1], angles=[0], levels=256, symmetric=True, normed=True)
        texture_contrast = graycoprops(glcm, 'contrast')[0, 0]
        texture_homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
        
        # 4. MORPHOLOGY (Lesion Shapes)
        # Mask for disease (same logic as before)
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        disease_mask = cv2.bitwise_and(thresh, cv2.bitwise_not(green_mask))
        
        # Find contours of spots
        contours, _ = cv2.findContours(disease_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        lesion_count = len(contours)
        avg_circularity = 0
        avg_area = 0
        
        valid_spots = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 10: # Ignore tiny noise
                perimeter = cv2.arcLength(cnt, True)
                if perimeter > 0:
                    # Circularity = 4 * pi * Area / (Perimeter^2)
                    # 1.0 = Perfect Circle, < 0.5 = Irregular/Splotchy
                    circularity = (4 * np.pi * area) / (perimeter * perimeter)
                    avg_circularity += circularity
                    avg_area += area
                    valid_spots += 1
        
        if valid_spots > 0:
            avg_circularity /= valid_spots
            avg_area /= valid_spots

        # 5. Generate Heatmap (Same as before)
        heatmap = img.copy()
        heatmap[disease_mask > 0] = [0, 0, 255] # Red BGR
        blended = cv2.addWeighted(img, 0.7, heatmap, 0.3, 0)
        filename = os.path.basename(image_path)
        heatmap_path = f"uploads/heatmap_{filename}"
        cv2.imwrite(heatmap_path, blended)

        return {
            "gli_index": round(avg_gli, 3),          # Green Leaf Index (-1 to 1)
            "texture_contrast": round(texture_contrast, 1), # High = Rough
            "texture_homogeneity": round(texture_homogeneity, 2), # High = Smooth
            "lesion_count": lesion_count,
            "avg_spot_area_px": round(avg_area, 0),
            "avg_circularity": round(avg_circularity, 2), # 1.0 = Circle
            "heatmap_url": heatmap_path,
            "severity": round((cv2.countNonZero(disease_mask)/cv2.countNonZero(thresh))*100, 2) if cv2.countNonZero(thresh) > 0 else 0
        }

    except Exception as e:
        print(f"CV Error: {e}")
        return {} # Return empty if fails

# --- UPDATE: /predict/advanced ENDPOINT ---
# --- CORRECTED ENDPOINT ---
@app.post("/predict/advanced")
async def predict_advanced(
    user_id: int = Form(...),
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    if model is None:
        raise HTTPException(status_code=503, detail="AI Model is offline")

    try:
        # 1. Read & Save Original
        contents = await file.read()
        ext = os.path.splitext(file.filename)[1]
        file_location = f"uploads/{uuid.uuid4()}{ext}"
        
        # Ensure uploads directory exists
        os.makedirs("uploads", exist_ok=True) 
        
        with open(file_location, "wb") as buffer:
            buffer.write(contents)

        # 2. RUN AI MODEL (Classification)
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        image = image.resize((224, 224))
        img_array = np.asarray(image)
        batch = np.array([img_array])

        predictions = model.predict(batch)
        scores = tf.nn.softmax(predictions[0]).numpy()
        
        class_probs = []
        for i, score in enumerate(scores):
            # FIX: Clean the name to remove numbering (e.g., "3. Gray Blight" -> "Gray Blight")
            raw_name = class_names[i]
            clean_name = raw_name
            
            # Check if name starts with a number followed by a dot and space (e.g. "3. ")
            if ". " in raw_name and raw_name.split(". ")[0].isdigit():
                clean_name = raw_name.split(". ", 1)[1]

            class_probs.append({
                "disease": clean_name, 
                "probability": float(score) * 100
            })
            
        class_probs.sort(key=lambda x: x["probability"], reverse=True)
        top_result = class_probs[0]

        # 3. RUN COMPUTER VISION (Quantification)
        # FIX: Calling the correct function 'analyze_lesions_advanced'
        cv_metrics = analyze_lesions_advanced(file_location)

        # FIX: Check if analysis failed (returned empty dict)
        if not cv_metrics:
            # Fallback values if CV fails
            cv_metrics = {
                "severity": 0,
                "lesion_count": 0,
                "heatmap_url": "",
                "gli_index": 0,
                "texture_contrast": 0,
                "texture_homogeneity": 0,
                "avg_circularity": 0,
                "avg_spot_area_px": 0
            }

        # 4. Save Report
        new_report = DiseaseReport(
            user_id=user_id,
            disease_name=top_result["disease"], # This will now save the clean name to DB
            confidence=f"{top_result['probability']:.1f}%",
            image_url=file_location,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            verification_status="Pending"
        )
        db.add(new_report)
        db.commit()

        # 5. Return Advanced Data
        return {
            "report_id": new_report.report_id,
            "top_diagnosis": top_result,
            "full_spectrum": class_probs[:5],
            "image_url": file_location,
            "telemetry": cv_metrics,
            
            # Scientific Metrics (Safe Access)
            "severity_metrics": {
                "score": cv_metrics.get("severity", 0),
                "lesion_count": cv_metrics.get("lesion_count", 0),
                "heatmap_url": cv_metrics.get("heatmap_url", "")
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc() # This prints the REAL error to your terminal
        print(f"Advanced Scan Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- UPDATE: EXPORT SCIENTIFIC REPORT (With Confusion & Telemetry) ---
@app.get("/api/reports/{report_id}/export")
def export_report_pdf(report_id: int, db: Session = Depends(get_db)):
    report = db.query(DiseaseReport).filter(DiseaseReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # 1. Re-calculate Advanced CV Metrics (The "Bio-Optical" Data)
    # Uses the advanced function we created earlier
    cv_metrics = analyze_lesions_advanced(report.image_url)
    
    # 2. Re-run AI Inference (To get Confusion/Confidence Spectrum)
    # We need to load the image and run it through the model again to get the full probability list
    confusion_spectrum = []
    try:
        if model:
            # Load and Preprocess
            img = Image.open(report.image_url).convert('RGB')
            img = img.resize((224, 224))
            img_array = np.asarray(img)
            batch = np.array([img_array])

            # Predict
            predictions = model.predict(batch)
            scores = tf.nn.softmax(predictions[0]).numpy()
            
            # Map to classes
            class_probs = []
            for i, score in enumerate(scores):
                class_probs.append({"name": class_names[i], "prob": float(score) * 100})
            
            # Sort and take Top 5
            class_probs.sort(key=lambda x: x["prob"], reverse=True)
            confusion_spectrum = class_probs[:5]
    except Exception as e:
        print(f"AI Re-inference failed: {e}")

    # 3. Generate PDF
    pdf_filename = f"uploads/Report_{report_id}.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter

    # --- HEADER ---
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "TeaCare Digital Pathology Report")
    
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.gray)
    c.drawString(50, height - 70, "Automated diagnostics generated by TeaCare Research Engine v2.0")
    c.setFillColor(colors.black)

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Report ID: #{report_id}")
    c.drawString(50, height - 120, f"Date: {report.timestamp}")
    c.drawString(300, height - 100, f"Analyst ID: {report.user_id}")
    c.drawString(300, height - 120, f"Location: {report.latitude}, {report.longitude}")

    c.setStrokeColor(colors.indigo)
    c.setLineWidth(2)
    c.line(50, height - 140, 550, height - 140)

    # --- SECTION 1: PRIMARY DIAGNOSIS ---
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 170, "1. Primary Diagnosis")
    
    # Box for result
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(50, height - 230, 500, 50, stroke=1, fill=0)
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(70, height - 200, f"{report.disease_name}")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(530, height - 200, f"{report.confidence}")
    c.setFont("Helvetica", 10)
    c.drawRightString(530, height - 215, "Confidence Score")

    # --- SECTION 2: AI CONFUSION SPECTRUM (New!) ---
    y_pos = height - 270
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_pos, "2. AI Confusion Spectrum")
    y_pos -= 25
    
    c.setFont("Helvetica", 10)
    c.drawString(50, y_pos, "Top 5 Candidate Diseases (Probability Distribution):")
    y_pos -= 20

    for item in confusion_spectrum:
        # Draw Bar Background
        c.setFillColor(colors.whitesmoke)
        c.rect(150, y_pos - 8, 300, 10, fill=1, stroke=0)
        
        # Draw Bar Foreground (Probability)
        bar_width = (item["prob"] / 100) * 300
        if item["name"] == report.disease_name:
            c.setFillColor(colors.indigo) # Winner is Indigo
        else:
            c.setFillColor(colors.gray)   # Others are Gray
            
        c.rect(150, y_pos - 8, bar_width, 10, fill=1, stroke=0)
        
        # Text Labels
        c.setFillColor(colors.black)
        c.drawString(50, y_pos, f"{item['name']}")
        c.drawString(460, y_pos, f"{item['prob']:.1f}%")
        
        y_pos -= 20

    # --- SECTION 3: BIO-OPTICAL TELEMETRY (New Data!) ---
    y_pos -= 20
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_pos, "3. Bio-Optical Telemetry")
    y_pos -= 30

    # Create a grid for metrics
    # Row 1: Infection Stats
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y_pos, "Infection Severity")
    c.drawString(200, y_pos, "Lesion Count")
    c.drawString(340, y_pos, "Avg Spot Size")
    
    c.setFont("Helvetica", 12)
    c.drawString(60, y_pos - 15, f"{cv_metrics.get('severity', 0)}%")
    c.drawString(200, y_pos - 15, f"{cv_metrics.get('lesion_count', 0)}")
    c.drawString(340, y_pos - 15, f"{cv_metrics.get('avg_spot_area_px', 0)} px")

    y_pos -= 40
    
    # Row 2: Advanced Morphology
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y_pos, "Green Leaf Index (GLI)")
    c.drawString(200, y_pos, "Texture (Contrast)")
    c.drawString(340, y_pos, "Circularity (0-1)")
    
    c.setFont("Helvetica", 12)
    c.drawString(60, y_pos - 15, f"{cv_metrics.get('gli_index', 'N/A')}")
    c.drawString(200, y_pos - 15, f"{cv_metrics.get('texture_contrast', 'N/A')}")
    c.drawString(340, y_pos - 15, f"{cv_metrics.get('avg_circularity', 'N/A')}")

    # --- SECTION 4: VISUAL EVIDENCE ---
    y_pos -= 60
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_pos, "4. Visual Evidence")
    
    try:
        # Draw Original
        c.drawImage(report.image_url, 50, y_pos - 220, width=200, height=200, preserveAspectRatio=True)
        c.setFont("Helvetica", 10)
        c.drawString(50, y_pos - 235, "Fig A: Original Specimen")
        
        # Draw Heatmap (if available)
        if 'heatmap_url' in cv_metrics and os.path.exists(cv_metrics['heatmap_url']):
            c.drawImage(cv_metrics['heatmap_url'], 300, y_pos - 220, width=200, height=200, preserveAspectRatio=True)
            c.drawString(300, y_pos - 235, "Fig B: Computer Vision Heatmap")
    except Exception as e:
        print(f"PDF Image Error: {e}")

    # --- FOOTER ---
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 30, f"Generated automatically by TeaCare System on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.drawRightString(550, 30, "Page 1 of 1")

    c.save()
    
    return FileResponse(pdf_filename, media_type='application/pdf', filename=f"TeaCare_Report_{report_id}.pdf")