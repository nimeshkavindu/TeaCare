from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
from sqlalchemy import create_engine, Column, Integer, String, Float, or_
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

# --- DATABASE CONFIG ---
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin123@localhost/teacare_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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

Base.metadata.create_all(bind=engine)

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

# --- APP SETUP ---
app = FastAPI()
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- HELPER: BLUR CHECK ---
def is_blurry(image_bytes, threshold=35.0):
    # Convert bytes to numpy array for OpenCV
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    # Calculate Variance of Laplacian
    score = cv2.Laplacian(img, cv2.CV_64F).var()
    
    # LOG THE SCORE (So you can tune it)
    print(f"DEBUG: Blur Score = {score:.2f}") 
    
    return score < threshold

# --- LOAD AI MODEL ---
print("Loading AI Model...")
try:
    model = tf.keras.models.load_model('tea_leaf_efficientnet.keras')
    with open('class_names.pkl', 'rb') as f:
        class_names = pickle.load(f)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    class_names = ["Error"] * 10 


# --- PREDICTION ENDPOINT (WITH TTA & BLUR CHECK) ---
@app.post("/predict")
async def predict_disease(
    user_id: int = Form(...),
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    try:
        # 1. Read Content
        contents = await file.read()
        
        # 2. Check for Blur
        if is_blurry(contents):
            return {
                "error": "Image is too blurry. Please hold the camera steady and try again.",
                "blur_score": "Low"
            }

        # 3. Save File
        file_location = f"uploads/{file.filename}"
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

        db_disease_name = re.sub(r'^\d+\.\s*', '', disease_name).strip() 
        
        # 6. FETCH DYNAMIC DATA FROM DB (Using the clean name)
        disease_info = db.query(DiseaseInfo).filter(DiseaseInfo.name.ilike(db_disease_name)).first()
        
        if disease_info:
            symptoms = disease_info.symptoms
            causes = disease_info.causes
            
            treatments_db = db.query(Treatment).filter(Treatment.disease_id == disease_info.disease_id).all()
            treatment_list = [
                {
                    "type": t.type,
                    "title": t.title,
                    "instruction": t.instruction,
                    "safety_tip": t.safety_tip
                } for t in treatments_db
            ]
        else:
            symptoms = ["Leaf appears healthy"] if disease_name == "Healthy Leaf" else []
            causes = []
            treatment_list = []

        # --- MISSING PART RESTORED BELOW ---
        
        # 7. Save Report to Database
        new_report = DiseaseReport(
            user_id=user_id,
            disease_name=disease_name,
            confidence=f"{confidence:.1f}%",
            image_url=file_location,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report) # Needed to get the new 'report_id'
        
        # -----------------------------------

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
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- NEW: UPDATE LOCATION ---
@app.patch("/history/{report_id}/location")
def update_location(report_id: int, loc: LocationUpdate, db: Session = Depends(get_db)):
    report = db.query(DiseaseReport).filter(DiseaseReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.latitude = loc.latitude
    report.longitude = loc.longitude
    db.commit()
    return {"message": "Location saved"}

# --- NEW: SUBMIT FEEDBACK (Active Learning) ---
@app.post("/history/{report_id}/feedback")
def submit_feedback(report_id: int, feedback: FeedbackRequest, db: Session = Depends(get_db)):
    report = db.query(DiseaseReport).filter(DiseaseReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.is_correct = "Yes" if feedback.is_correct else "No"
    if not feedback.is_correct:
        report.user_correction = feedback.correct_disease
        # In a real app, you would move the image to a "retrain" folder here
    
    db.commit()
    return {"message": "Feedback received"}

# ... (Keep your existing Register, Login, History, Weather, Forum endpoints below) ...
@app.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    c_type = user.contact_type.lower()
    c_val = user.contact_value.lower() if c_type == 'email' else user.contact_value

    existing_user = db.query(User).filter(
        or_(User.phone_number == c_val, User.email == c_val)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already registered")

    new_phone = c_val if c_type == "phone" else None
    new_email = c_val if c_type == "email" else None
    hashed_secret = get_password_hash(user.secret)

    new_user = User(full_name=user.full_name, phone_number=new_phone, email=new_email, password_hash=hashed_secret, role=user.role)
    db.add(new_user)
    db.commit()
    return {"message": "Registration successful"}

@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    ident = request.identifier.lower() if "@" in request.identifier else request.identifier
    user = db.query(User).filter(or_(User.phone_number == ident, User.email == ident)).first()

    if not user or not verify_password(request.secret, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Login successful", "user_id": user.user_id, "name": user.full_name, "role": user.role}

@app.get("/history/{user_id}")
def get_history(user_id: int, db: Session = Depends(get_db)):
    return db.query(DiseaseReport).filter(DiseaseReport.user_id == user_id).order_by(DiseaseReport.report_id.desc()).all()

@app.get("/weather")
def get_weather_alert():
    return {
        "location": "Kandy, Sri Lanka", "temperature": 22, "humidity": 85, 
        "condition": "Rainy", "risk_level": "High", "disease_forecast": "Blister Blight",
        "advice": "High humidity detected. Avoid plucking wet leaves."
    }