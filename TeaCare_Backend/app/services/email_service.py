from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings

# --- EMAIL CONFIGURATION ---
email_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    
    # Standard Gmail Settings 
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_otp_email(email: str, otp: str):
    """
    Sends an HTML email with the verification OTP.
    """
    message = MessageSchema(
        subject="TeaCare Verification Code",
        recipients=[email],
        body=f"<h3>Your TeaCare Verification Code</h3><p>Your OTP is: <strong>{otp}</strong></p><p>It expires in 10 minutes.</p>",
        subtype=MessageType.html
    )
    
    fm = FastMail(email_conf)
    await fm.send_message(message)