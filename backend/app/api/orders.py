from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.order_service import OrderService
from langfuse import observe

router = APIRouter()

@router.post("/orders")
@observe(name="create_order_api")
def create_order(payload: dict, db: Session = Depends(get_db)):
    """
    API endpoint to create an order.
    The database session (db) is injected automatically by FastAPI.
    """
    service = OrderService(db)
    return service.create_order(**payload)

# --- NEW LEVEL-1 ADDITION ---
@router.get("/orders/history/{patient_id}")
@observe(name="get_order_history_api")
def get_order_history(patient_id: str, db: Session = Depends(get_db)):
    """
    Fetches the order history for a specific patient directly from SQLite.
    """
    service = OrderService(db)
    return service.get_order_history(patient_id)