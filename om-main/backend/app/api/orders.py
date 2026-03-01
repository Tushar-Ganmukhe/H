from fastapi import APIRouter
from langfuse import observe
from app.services.order_service import OrderService

router = APIRouter()
service = OrderService()

@router.post("/orders")
@observe(name="create_order_api")
def create_order(payload: dict):
    return service.create_order(**payload)