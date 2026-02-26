from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import Patient
from pydantic import BaseModel
from langfuse import observe
# NEW: Import our robust external tools
from app.core.external_tools import ExternalTools

router = APIRouter(prefix="/auth", tags=["Auth"])

class AuthRequest(BaseModel):
    mobile: str
    name: str = None

@router.post("/register")
@observe(name="user_registration")
def register(req: AuthRequest, db: Session = Depends(get_db)):
    # 1. Check if user exists
    existing = db.query(Patient).filter(Patient.mobile == req.mobile).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    
    # 2. Save new user to SQLite
    new_user = Patient(name=req.name, mobile=req.mobile)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 3. TRIGGER AUTOMATIC WHATSAPP WELCOME MESSAGE
    welcome_msg = (
        f"🏥 Welcome to Pharmacy AI, {req.name or 'Valued Patient'}!\n\n"
        f"Your account is successfully registered with mobile: {req.mobile}.\n"
        f"You can now order medicines, check stock, and get instant AI consultations.\n\n"
        f"How can I help you today?"
    )
    
    # This safely attempts to send the message or falls back to console mock
    ExternalTools.send_whatsapp_message(to_mobile=req.mobile, message_body=welcome_msg)
    
    return {"name": new_user.name, "mobile": new_user.mobile, "role": "user"}

@router.post("/login")
@observe(name="user_login")
def login(req: AuthRequest, db: Session = Depends(get_db)):
    # Admin Bypass
    if req.mobile == "9999999999":
        return {"name": "Admin Pharmacist", "mobile": "9999999999", "role": "admin"}
        
    user = db.query(Patient).filter(Patient.mobile == req.mobile).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please register.")
    
    return {"name": user.name, "mobile": user.mobile, "role": "user"}