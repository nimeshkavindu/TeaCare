from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.sql_models import User, SystemLog
from app.schemas.dtos import UserRegister, LoginRequest, VerifyRequest, UserUpdate
from app.core.security import get_password_hash, verify_password, generate_otp
from app.services.email_service import send_otp_email
from app.services.sms_service import send_otp_sms

router = APIRouter()

# --- HELPER: LOGGING (Local to this module or imported if shared) ---
def log_event(db: Session, level: str, source: str, message: str):
    try:
        new_log = SystemLog(level=level, source=source, message=message)
        db.add(new_log)
        db.commit()
    except Exception as e:
        print(f"Logging failed: {e}")

# --- 1. REGISTER ---
@router.post("/register")
async def register(user: UserRegister, db: Session = Depends(get_db)):
    c_type = user.contact_type.lower()
    c_val = user.contact_value.lower() if c_type == 'email' else user.contact_value

    # Check if user exists
    existing_user = db.query(User).filter(
        or_(User.phone_number == c_val, User.email == c_val)
    ).first()
    
    if existing_user:
        # If user exists but NOT verified, delete old record to restart process
        if not existing_user.is_verified:
            db.delete(existing_user)
            db.commit()
        else:
            raise HTTPException(status_code=400, detail="User already registered")

    hashed_secret = get_password_hash(user.secret)
    otp = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=10)

    new_user = User(
        full_name=user.full_name,
        phone_number=c_val if c_type == "phone" else None,
        email=c_val if c_type == "email" else None,
        password_hash=hashed_secret,
        role=user.role.lower(),
        otp_code=otp,
        otp_expiry=expiry,
        is_verified=False 
    )
    db.add(new_user)
    db.commit()

    # Send OTP
    if c_type == "email":
        await send_otp_email(c_val, otp)
    elif c_type == "phone":
        await send_otp_sms(c_val, otp)
    
    return {"message": "OTP sent", "contact": c_val}

# --- 2. VERIFY OTP ---
@router.post("/verify-otp")
def verify_otp(req: VerifyRequest, db: Session = Depends(get_db)):
    # Find User
    user = db.query(User).filter(
        or_(User.email == req.contact_value, User.phone_number == req.contact_value)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        return {"message": "Already verified"}

    # Check OTP
    if user.otp_code != req.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    if user.otp_expiry and datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="OTP Expired. Please register again.")

    # Activate User
    user.is_verified = True
    user.otp_code = None # Clear OTP
    db.commit()

    log_event(db, "SUCCESS", "Auth", f"User Verified: {user.full_name}")
    return {"message": "Verification Successful"}

# --- 3. LOGIN ---
@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    ident = request.identifier.lower() if "@" in request.identifier else request.identifier
    user = db.query(User).filter(or_(User.phone_number == ident, User.email == ident)).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if Banned
    if not user.is_active:
        log_event(db, "WARNING", "Auth", f"Blocked login attempt by BANNED user: {ident}")
        raise HTTPException(status_code=403, detail="Your account has been suspended. Contact Admin.")

    # Verify Password
    if not verify_password(request.secret, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check Verification Status (Optional: Prevent login if unverified)
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Account not verified. Please verify OTP.")

    # Update Last Login
    user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M")
    db.commit()

    log_event(db, "SUCCESS", "Auth", f"User logged in: {user.full_name}")
    return {
        "message": "Login successful", 
        "user_id": user.user_id, 
        "name": user.full_name, 
        "role": user.role
    }

# --- 4. UPDATE PROFILE ---
@router.put("/users/{user_id}")
def update_user_profile(user_id: int, update_data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if update_data.full_name:
        user.full_name = update_data.full_name
    
    if update_data.secret:
        user.password_hash = get_password_hash(update_data.secret)
    
    db.commit()
    log_event(db, "INFO", "User Mgmt", f"User {user_id} updated profile")
    return {"message": "Profile updated successfully"}