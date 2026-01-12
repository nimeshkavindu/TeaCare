from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
from sqlalchemy import create_engine, Column, Integer, String, Float, or_, text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker, Session
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

class ForumPost(Base):
    __tablename__ = "forum_posts"
    post_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    author_name = Column(String)
    title = Column(String)
    content = Column(String)
    image_url = Column(String, nullable=True)
    timestamp = Column(String)
    likes = Column(Integer, default=0) 

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
    name = Column(String)
    symptoms = Column(postgresql.ARRAY(String)) 
    causes = Column(postgresql.ARRAY(String))

class Treatment(Base):
    __tablename__ = "treatments"
    treatment_id = Column(Integer, primary_key=True)
    disease_id = Column(Integer)
    type = Column(String)
    title = Column(String)
    instruction = Column(String)
    safety_tip = Column(String)

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

        
        # 7. Save Report
        new_report = DiseaseReport(
            user_id=user_id,
            disease_name=disease_name,
            confidence=f"{confidence:.1f}%",
            image_url=file_location,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
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
    
    db.commit()
    
    # --- LOG FEEDBACK ---
    status = "Correct" if feedback.is_correct else f"Incorrect (User said: {feedback.correct_disease})"
    log_event(db, "INFO", "Feedback", f"Report #{report_id} marked as {status}")
    
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
@app.post("/posts")
def create_post(
    user_id: int = Form(...),
    author_name: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    file: UploadFile = File(None), 
    db: Session = Depends(get_db)
):
    image_path = None
    if file:
        ext = os.path.splitext(file.filename)[1]
        file_location = f"uploads/{uuid.uuid4()}{ext}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        image_path = file_location

    new_post = ForumPost(
        user_id=user_id,
        author_name=author_name,
        title=title,
        content=content,
        image_url=image_path, 
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    db.add(new_post)
    db.commit()
    
    log_event(db, "SUCCESS", "Forum", f"New Post ID {new_post.post_id} by User {user_id}")
    return {"message": "Post created successfully"}

@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(ForumPost).order_by(ForumPost.post_id.desc()).all()
    return posts

@app.post("/posts/{post_id}/like")
def like_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(ForumPost).filter(ForumPost.post_id == post_id).first()
    if not post: raise HTTPException(status_code=404, detail="Post not found")
    post.likes += 1
    db.commit()
    return {"likes": post.likes}

@app.post("/comments")
def add_comment(request: CommentRequest, db: Session = Depends(get_db)):
    new_comment = ForumComment(
        post_id=request.post_id,
        user_id=request.user_id,
        author_name=request.author_name,
        content=request.content,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    db.add(new_comment)
    db.commit()
    
    log_event(db, "SUCCESS", "Forum", f"Comment added to Post {request.post_id} by {request.author_name}")
    return {"message": "Comment added"}

@app.get("/posts/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db)):
    return db.query(ForumComment).filter(ForumComment.post_id == post_id).all()

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