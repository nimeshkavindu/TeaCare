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
import httpx
from llama_cpp import Llama
from fastapi.responses import StreamingResponse
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from fastembed import TextEmbedding
from pypdf import PdfReader

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

# --- VECTOR DATABASE SETUP (Custom FastEmbed Wrapper) ---
print("Initializing Vector Database (FastEmbed Mode)...")

# 1. Define the Wrapper Class manually
class MyFastEmbedFunction(EmbeddingFunction):
    def __init__(self):
        # Automatically downloads the lightweight model
        self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    
    def __call__(self, input: Documents) -> Embeddings:
        # Converts text to vector numbers
        return list(self.model.embed(input))

# 2. Setup Storage
chroma_client = chromadb.PersistentClient(path="./tea_vectordb")

# 3. Create Collection using our Custom Wrapper
knowledge_collection = chroma_client.get_or_create_collection(
    name="tea_knowledge",
    embedding_function=MyFastEmbedFunction()
)
print("✅ Vector Database Ready!")

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
model = None  

try:
    model = tf.keras.models.load_model('tea_leaf_efficientnet.keras')
    with open('class_names.pkl', 'rb') as f:
        class_names = pickle.load(f)
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    class_names = ["Error"] * 10


# --- PREDICTION ENDPOINT (WITH TTA & BLUR CHECK) ---
@app.post("/predict")
async def predict_disease(
    user_id: int = Form(...),
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    
    if model is None:
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
        
        # Check if confidence is too low (less than 50%)
        if confidence < 50:
            disease_name = "Unknown / Unclear"
            symptoms = ["The AI is not sure. The image might be unclear, or this disease is not in our database."]
            causes = ["Low image quality", "Unrecognized pattern"]
            treatment_list = []
            
            print(f"Low confidence detection ({confidence:.2f}%) for user {user_id}")

        else:
            db_disease_name = re.sub(r'^\d+\.\s*', '', disease_name).strip() 
            disease_name = db_disease_name
            # 6. FETCH DYNAMIC DATA FROM DB
            disease_info = db.query(DiseaseInfo).filter(DiseaseInfo.name.ilike(disease_name)).first()
            
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
                symptoms = ["Leaf appears healthy"] if "Healthy" in disease_name else ["No details available for this disease."]
                causes = []
                treatment_list = []

        
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
        db.refresh(new_report) 
        
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

# --- UPDATE LOCATION ---
@app.patch("/history/{report_id}/location")
def update_location(report_id: int, loc: LocationUpdate, db: Session = Depends(get_db)):
    report = db.query(DiseaseReport).filter(DiseaseReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.latitude = loc.latitude
    report.longitude = loc.longitude
    db.commit()
    return {"message": "Location saved"}

# --- PUBLIC MAP ENDPOINT ---
@app.get("/reports/locations")
def get_public_reports(db: Session = Depends(get_db)):
    # Return all reports that have a location saved
    reports = db.query(DiseaseReport).filter(DiseaseReport.latitude != None).all()
    return reports

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

# --- WEATHER ENDPOINT ---
@app.get("/weather")
async def get_weather_alert(lat: float = 6.9271, lng: float = 79.8612):
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

@app.post("/posts/{post_id}/like")
def like_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(ForumPost).filter(ForumPost.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
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
    return {"message": "Comment added"}

@app.get("/posts/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db)):
    return db.query(ForumComment).filter(ForumComment.post_id == post_id).all()

# --- AI ENGINE ---
print("Loading LLM...")
llm = Llama(
    model_path="models/qwen2.5-1.5b-instruct-q4_k_m.gguf", 
    n_ctx=2048,      # Context window 
    n_threads=4,     # CPU threads to use
    verbose=False
)
print("LLM is Ready!")

# --- CHATBOT LOGIC ---

# 1. PDF Upload Endpoint 
@app.post("/upload_book")
async def upload_book(file: UploadFile = File(...), category: str = Form("General")):
    print(f"📥 Receiving PDF: {file.filename}...")

    # A. Read PDF Text
    try:
        pdf_reader = PdfReader(file.file)
        full_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        
        print(f"📖 Extracted {len(full_text)} characters.")

        # B. Chunking 
        chunk_size = 1000
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        
        print(f"✂️ Sliced into {len(chunks)} chunks.")

        # C. Save to ChromaDB
        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{file.filename}_part_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "source": file.filename,
                "category": category
            })

        knowledge_collection.add(ids=ids, documents=documents, metadatas=metadatas)
        print("✅ Knowledge stored in Vector Database!")
        
        return {"message": f"Successfully learned {len(chunks)} chunks from '{file.filename}'."}

    except Exception as e:
        print(f"❌ PDF Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process PDF")

# 2. Semantic Search Function
def retrieve_context(query: str, db: Session):
    print(f"\n🧠 SEMANTIC SEARCH FOR: '{query}'")

    # A. Query Vector DB (Chroma)
    results = knowledge_collection.query(
        query_texts=[query],
        n_results=1 
    )

    context_list = []

    # Check Vector Results
    if results['documents'] and results['documents'][0]:
        print(f"✅ FOUND {len(results['documents'][0])} MATCHES:")
        for i, doc in enumerate(results['documents'][0]):
            source = results['metadatas'][0][i]['source']
            context_list.append(f"Fact: {doc} (Source: {source})")
            print(f"   [{i+1}] {doc[:100]}...")
    else:
        print("❌ NO VECTOR MATCHES.")

    # B. Append Disease Info (from SQL) for backup
    clean_query = query.replace("?", "").replace(".", "")
    diseases = db.query(DiseaseInfo).filter(DiseaseInfo.name.ilike(f"%{clean_query}%")).limit(1).all()
    for d in diseases:
        context_list.append(f"Disease Info: {d.name}. Symptoms: {', '.join(d.symptoms)}.")

    if not context_list:
        return "NO_DATA_FOUND"

    return "\n\n".join(context_list)

# 3. Chat Endpoint (Strict Generation)
@app.post("/chat_stream")
async def chat_stream(
    user_query: str = Form(...),
    db: Session = Depends(get_db)
):
    # Step 1: Find Context (Vector + SQL)
    context = retrieve_context(user_query, db)
    
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
    
    # Step 3: Generate Stream
    def iter_tokens():
        stream = llm(
            prompt,
            max_tokens=256, 
            stop=["<|im_end|>"],
            stream=True,
            temperature=0.5
        )
        for output in stream:
            yield output['choices'][0]['text']

    return StreamingResponse(iter_tokens(), media_type="text/plain")
