from passlib.context import CryptContext
import random
import string

# --- PASSWORD CONFIGURATION ---
# Using Argon2 as it is the current standard for secure password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against the hashed version.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hashes a password using Argon2.
    """
    return pwd_context.hash(password)

def generate_otp(length: int = 6) -> str:
    """
    Generates a numeric OTP (One Time Password) of specified length.
    """
    return ''.join(random.choices(string.digits, k=length))