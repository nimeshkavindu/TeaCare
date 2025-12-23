from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
from sqlalchemy import create_engine, Column, Integer, String, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
import shutil
import os
import tensorflow as tf
import numpy as np
from PIL import Image
import io
from datetime import datetime
from fastapi import Form 
import pickle
import uvicorn
import re

#DBConfig
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

Base.metadata.create_all(bind=engine)

# --- VALIDATION SCHEMAS ---
class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    contact_type: str 
    contact_value: str 
    secret: str        

    @validator('contact_value')
    def validate_contact(cls, v, values):
        ctype = values.get('contact_type', '').lower()
        if ctype == 'email':
            # Simple Email Regex
            if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
                raise ValueError("Invalid email address format")
        elif ctype == 'phone':
            # Allow digits, +, -, space. Min 9 digits.
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

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# endpoint message
@app.get("/")
def read_root():
    return {"message": "TeaCare Backend is Running!"}

@app.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    # 1. Normalize Inputs
    c_type = user.contact_type
    c_val = user.contact_value.lower() if c_type == 'email' else user.contact_value

    # 2. Check if user exists
    existing_user = db.query(User).filter(
        or_(User.phone_number == c_val, User.email == c_val)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already registered with this phone/email")

    # 3. Prepare Data
    new_phone = c_val if c_type == "phone" else None
    new_email = c_val if c_type == "email" else None
    
    # 4. Hash Password (Argon2)
    hashed_secret = get_password_hash(user.secret)

    # 5. Save
    new_user = User(
        full_name=user.full_name,
        phone_number=new_phone,
        email=new_email,
        password_hash=hashed_secret,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    return {"message": "Registration successful"}

@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # 1. Find user by Email OR Phone
    user = db.query(User).filter(
        or_(User.phone_number == request.identifier, User.email == request.identifier)
    ).first()

    # 2. Verify
    if not user or not verify_password(request.secret, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "message": "Login successful",
        "user_id": user.user_id,
        "name": user.full_name,
        "role": user.role
    }

# --- 1. LOAD THE MODEL & CLASSES ---
print("Loading AI Model...")
try:
    # Load the trained model
    model = tf.keras.models.load_model('tea_leaf_efficientnet.keras')
    
    # Load class names
    with open('class_names.pkl', 'rb') as f:
        class_names = pickle.load(f)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    class_names = ["Error"] * 10 # Fallback

# --- 2. PREDICTION ENDPOINT ---
@app.post("/predict")
async def predict_disease(
    file: UploadFile = File(...), 
    user_id: int = Form(...) # We need to know who scanned it
):
    try:
        # A. Read and Preprocess Image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        
        # Resize to 224x224 (EfficientNet standard)
        image = image.resize((224, 224))
        img_array = np.asarray(image)
        img_reshape = img_array[np.newaxis, ...] # Add batch dimension
        
        # B. Make Prediction
        prediction = model.predict(img_reshape)
        score = tf.nn.softmax(prediction[0])
        
        # Get result
        class_idx = np.argmax(score)
        disease_name = class_names[class_idx]
        confidence = float(np.max(score)) * 100
        
        # C. Define Simple Treatments (expand this DB)
        treatments = {
            "Red Spider": "Spray sulfur-based miticides and maintain humidity.",
            "Brown Blight": "Improve drainage and apply copper fungicides.",
            "Gray Blight": "Prune infected areas and apply carbendazim.",
            "Tea Algal Leaf Spot": "Improve air circulation and reduce shade.",
            "Helopeltis": "Apply systemic insecticides early morning.",
            "Green Mirid Bug": "Use pheromone traps and neem oil.",
            "Healthy Leaf": "Keep up the good work! Maintain regular watering."
        }
        treatment = treatments.get(disease_name, "Consult an agricultural expert.")
        
        # D. Save to Database (History)
        # Assuming you have a DB session 'db' available (you might need to inject it)
        # For this snippet, we'll just return the data for the UI
        
        return {
            "disease_name": disease_name,
            "confidence": f"{confidence:.2f}%",
            "treatment": treatment,
            "symptoms": ["Visual discoloration", "Texture change"] # Placeholder
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# upload files
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")



#Recent scans
@app.get("/history/{user_id}")
def get_history(user_id: int, db: Session = Depends(get_db)):
    reports = db.query(DiseaseReport)\
                .filter(DiseaseReport.user_id == user_id)\
                .order_by(DiseaseReport.report_id.desc())\
                .all()
    return reports

#Weather 
@app.get("/weather")
def get_weather_alert():
    return {
        "location": "Kandy, Sri Lanka",
        "temperature": 22,
        "humidity": 85, 
        "condition": "Rainy",
        "risk_level": "High", 
        "disease_forecast": "Blister Blight",
        "advice": "High humidity detected. Avoid plucking wet leaves and apply preventive fungicide."
    }

#Community Forum

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
        file_location = f"uploads/{file.filename}"
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
    return {"message": "Post created successfully"}

@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(ForumPost).order_by(ForumPost.post_id.desc()).all()
    return posts

# Like and comment

@app.post("/posts/{post_id}/like")
def like_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(ForumPost).filter(ForumPost.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.likes += 1
    db.commit()
    return {"likes": post.likes}

class CommentRequest(BaseModel):
    post_id: int
    user_id: int
    author_name: str
    content: str

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
    return {"message": "Comment added"}

@app.get("/posts/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db)):
    return db.query(ForumComment).filter(ForumComment.post_id == post_id).all()