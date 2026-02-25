import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from langfuse import observe
from app.core.models import Order, Product

class OrderService:
    def __init__(self, db: Session):
        self.db = db

    @observe(name="create_order_service")
    def create_order(self, patient_id, product_id, quantity, total_price):
        product = self.db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            return {"error": "Product not found in database."}

        if product.stock < quantity:
            return {"error": f"Insufficient stock. Only {product.stock} units left."}

        product.stock -= int(quantity)
        product.last_updated = datetime.utcnow()

        order_id = str(uuid.uuid4())
        new_order = Order(
            order_id=order_id,
            patient_id=str(patient_id),
            product_id=product.product_id,
            product_name=product.name,
            quantity=int(quantity),
            total_price=float(total_price),
            created_at=datetime.utcnow()
        )

        try:
            self.db.add(new_order)
            self.db.commit()
            self.db.refresh(new_order)
            return {
                "order_id": new_order.order_id,
                "patient_id": new_order.patient_id,
                "product_name": new_order.product_name,
                "quantity": new_order.quantity,
                "total_price": new_order.total_price,
                "created_at": new_order.created_at,
                "status": "SUCCESS"
            }
        except Exception as e:
            self.db.rollback()
            return {"error": f"Failed to save order: {str(e)}"}

    @observe(name="get_order_history_service")
    def get_order_history(self, patient_id: str):
        return self.db.query(Order).filter(Order.patient_id == patient_id).order_by(Order.created_at.desc()).all()

    @observe(name="get_last_order_service")
    def get_last_order(self, patient_id: str):
        """Fetches the most recent order for a mobile number."""
        return self.db.query(Order).filter(Order.patient_id == patient_id).order_by(Order.created_at.desc()).first()