from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.core.database import SessionLocal
from app.core.external_tools import ExternalTools

class ExecutionAgent:
    def __init__(self):
        self.db = SessionLocal()
        self.products = ProductService(self.db)
        self.orders = OrderService(self.db)

    def prepare_order(self, product_name: str, quantity: int):
        """Stage 1: Validate and Quote (No DB Write)"""
        prod = self.products.get_product_by_name(product_name)
        if not prod:
            return {"success": False, "error": "Medicine not found"}
        if prod['stock'] < quantity:
            return {"success": False, "error": f"Only {prod['stock']} available"}
        
        total = round(prod['price'] * quantity, 2)
        return {
            "success": True, 
            "product_id": prod['product_id'],
            "price": prod['price'],
            "total": total,
            "msg": f"Order for {quantity}x {prod['product_name']} comes to ${total}. Confirm?"
        }

    async def commit_order(self, patient_id: str, product_id: str, quantity: int, total: float):
        """Stage 2: Finalize (Subtract Stock & Notify)"""
        res = self.orders.create_order(patient_id, product_id, quantity, total)
        if "order_id" in res:
            ExternalTools.send_whatsapp_message(patient_id, f"✅ Order Confirmed! ID: {res['order_id'][:8]}")
            return {"success": True, "order_id": res['order_id']}
        return {"success": False, "error": "Storage error"}