import httpx
from app.core.config import settings

async def send_otp_sms(phone: str, otp: str):
    url = "https://app.text.lk/api/v3/sms/send"
    
    # 1. Format Phone Number
    clean_phone = phone.replace("+", "").replace(" ", "").strip()
    if clean_phone.startswith("0"):
        clean_phone = "94" + clean_phone[1:]
    
    # Log the attempt
    print(f"👉 Sending SMS to: {clean_phone}")

    payload = {
        "recipient": clean_phone,
        "sender_id": settings.TEXTLK_SENDER_ID,
        "type": "plain",
        "message": f"Your TeaCare verification code is: {otp}"
    }
    
    headers = {
        "Authorization": f"Bearer {settings.TEXTLK_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            
            # Success Logs
            print(f"✅ SMS Sent! Status: {resp.status_code}")
            print(f"Response: {resp.text}")
            
        except Exception as e:
            print(f"⚠️ SMS Failed: {e}")
            # CRITICAL BACKUP: Print OTP to console if SMS fails
            print(f"👉 [BACKUP] OTP for {clean_phone}: {otp}")