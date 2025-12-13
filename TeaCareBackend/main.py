from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import shutil
import os
import tensorflow as tf
import numpy as np
from PIL import Image
import io
from datetime import datetime
from fastapi import Form 
import pickle


#DBConfig
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin123@localhost/teacare_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    phone_number = Column(String, unique=True)
    pin_hash = Column(String)
    role = Column(String, default="Farmer")


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

app = FastAPI()

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class LoginRequest(BaseModel):
    phone_number: str
    pin: str


class RegisterRequest(BaseModel):
    full_name: str
    phone_number: str
    pin: str


# upload files
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# endpoint message
@app.get("/")
def read_root():
    return {"message": "TeaCare Backend is Running!"}


@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == request.phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.pin_hash != request.pin:
        raise HTTPException(status_code=401, detail="Incorrect PIN")
    return {"message": "Login Successful", "name": user.full_name, "user_id": user.user_id}


@app.post("/register")
def register_farmer(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.phone_number == request.phone_number).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    new_user = User(
        full_name=request.full_name,
        phone_number=request.phone_number,
        pin_hash=request.pin,
        role="Farmer"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Registration Successful", "user_id": new_user.user_id}


@app.post("/predict")
async def predict_disease(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb") as buffer:
        file.file.seek(0)
        content = await file.read()
        buffer.write(content)

    image = Image.open(io.BytesIO(content)).convert('RGB')
    image = image.resize((224, 224))
    input_array = np.array(image, dtype=np.float32) / 255.0
    input_array = np.expand_dims(input_array, axis=0)

    interpreter.set_tensor(input_details[0]['index'], input_array)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])

    confidence_score = np.max(output_data) * 100
    predicted_index = np.argmax(output_data)

    MINIMUM_CONFIDENCE = 50.0

    if confidence_score < MINIMUM_CONFIDENCE:
        disease_name = "Unknown"
        treatment = "Image unclear. Please retake the photo."
        symptoms = ["No reliable disease signs detected."]
    else:
        disease_name = CLASS_NAMES[predicted_index]

        if disease_name == "Healthy Leaf":
            treatment = "No treatment needed."
            symptoms = ["Leaf appears healthy."]
        elif disease_name == "Tea Algal Leaf Spot":
            treatment = "Improve drainage and pruning. Apply Copper Oxychloride."
            symptoms = ["Greenish-grey spots", "Velvety texture"]
        elif disease_name == "Red Spider":
            treatment = "Spray Sulfur-based acaricides. Maintain humidity."
            symptoms = ["Reddish discoloration", "Webbing under leaves"]
        else:
            treatment = "Consult an expert or apply fungicide."
            symptoms = ["Disease patterns detected."]

    print(f"SAVING REPORT: User {user_id} - {disease_name} ({confidence_score:.2f}%)")

    new_report = DiseaseReport(
        user_id=user_id,
        disease_name=disease_name,
        confidence=f"{confidence_score:.1f}%",
        image_url=file_location,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    db.add(new_report)
    db.commit()

    return {
        "disease_name": disease_name,
        "confidence": f"{confidence_score:.1f}%",
        "symptoms": symptoms,
        "treatment": treatment,
        "image_url": file_location
    }

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