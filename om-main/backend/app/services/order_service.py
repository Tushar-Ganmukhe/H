import uuid
from datetime import datetime
from langfuse import observe

# This list holds new orders temporarily in memory
ORDERS = []

class OrderService:
    @observe(name="create_order_service")
    def create_order(self, patient_id, product_id, quantity, total_price, product_name=None):
        order = {
            "order_id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "product_id": product_id,
            "product_name": product_name, # ✅ Added product name
            "quantity": quantity,
            "total_price": total_price,
            "created_at": datetime.utcnow(),
            "status": "CREATED"
        }
        ORDERS.append(order)
        return order