from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from langfuse import observe
from app.agents.refill_agent import RefillAgent
from app.core.database import get_db
from app.core.models import Patient
from app.core.external_tools import ExternalTools

router = APIRouter(prefix="/refill", tags=["Refill Intelligence"])

# Request Model
class NotifyRequest(BaseModel):
    patient_id: str
    product_name: str
    message_type: str = "whatsapp" # or 'email'

@router.get("/refill-alerts")
@observe(name="get_refill_alerts_api")
def get_alerts():
    try:
        agent = RefillAgent()
        results = agent.check_refills()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Predictive Agent Error: {str(e)}")

@router.post("/notify")
@observe(name="trigger_refill_notification")
def send_notification(req: NotifyRequest, db: Session = Depends(get_db)):
    """
    Called by Admin Dashboard to manually trigger a proactive reminder.
    """
    # 1. Fetch Patient Details
    patient = db.query(Patient).filter(Patient.mobile == req.patient_id).first()
    
    # If not found in DB (maybe from excel history), use the ID as mobile directly
    mobile_number = patient.mobile if patient else req.patient_id
    patient_name = patient.name if patient else "Valued Customer"

    if req.message_type == "whatsapp":
        message = (
            f"👋 Hello {patient_name},\n\n"
            f"⚠️ Pharmacy Alert: Our AI predicts your **{req.product_name}** is running low.\n"
            f"Reply 'YES' to this message to reorder instantly."
        )
        res = ExternalTools.send_whatsapp_message(mobile_number, message)
        return {"status": "success", "details": res}

    elif req.message_type == "email":
        res = ExternalTools.send_email_message(
            f"{mobile_number}@example.com", 
            "Refill Reminder", 
            f"Time to refill {req.product_name}"
        )
        return {"status": "success", "details": res}
    
    return {"status": "error", "message": "Invalid type"}