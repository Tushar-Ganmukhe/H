from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import Patient
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Auth"])

class AuthRequest(BaseModel):
    mobile: str
    name: str = None

@router.post("/register")
def register(req: AuthRequest, db: Session = Depends(get_db)):
    existing = db.query(Patient).filter(Patient.mobile == req.mobile).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    
    new_user = Patient(name=req.name, mobile=req.mobile)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"name": new_user.name, "mobile": new_user.mobile, "role": "user"}

@router.post("/login")
def login(req: AuthRequest, db: Session = Depends(get_db)):
    # Admin Bypass
    if req.mobile == "9999999999":
        return {"name": "Admin Pharmacist", "mobile": "9999999999", "role": "admin"}
        
    user = db.query(Patient).filter(Patient.mobile == req.mobile).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please register.")
    
    return {"name": user.name, "mobile": user.mobile, "role": "user"}