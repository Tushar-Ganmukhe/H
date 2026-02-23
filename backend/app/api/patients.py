from fastapi import APIRouter
from langfuse import observe
from app.services.history_service import HistoryService

router = APIRouter()
service = HistoryService()

@router.get("/patients/{patient_ID}/history")
@observe(name="get_patient_history")
def get_history(patient_ID: str):
    return service.get_patient_history(patient_ID)
