import os
from langfuse import observe
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.vector_store import search_product
from app.core.database import SessionLocal
# NEW: Import the robust tools
from app.core.external_tools import ExternalTools

class ExecutionAgent:
    def __init__(self):
        # We open a database session specifically for the AI Agent
        self.db = SessionLocal()
        self.order_service = OrderService(self.db)
        self.product_service = ProductService(self.db)

    def calculate_total(self, price, qty):
        try:
            return round(float(price) * int(qty), 2)
        except:
            return 0

    @observe(name="order_execution_agent")
    async def execute_order(self, patient_id: int, product_name: str, quantity: int):
        """
        1. AI recognizes the medicine name.
        2. Queries SQLite DB (Real-time price & stock).
        3. Validates stock.
        4. Processes order via OrderService.
        5. Triggers Warehouse & Notification Tools.
        """
        if not product_name or str(product_name).strip() == "":
             return {
                "approved": False,
                "error": "I couldn't identify the medicine name. Please specify which medicine you need."
            }

        # 1. Resolve product name using vector search (Fuzzy match)
        resolved_name = search_product(product_name) or product_name
        
        # 2. Fetch REAL-TIME Product Details from Database
        product_data = self.product_service.get_product_by_name(resolved_name)

        if not product_data:
            return {
                "approved": False,
                "error": f"I'm sorry, I couldn't find '{product_name}' in our current inventory database."
            }

        # 3. Check Real-Time Stock (Sync with Admin Portal)
        if product_data["stock"] < int(quantity):
            return {
                "approved": False,
                "error": f"We currently only have {product_data['stock']} units of {product_data['product_name']} in stock. Would you like to order a smaller amount?"
            }

        # 4. Calculate Final Price using DB values
        total_price = self.calculate_total(product_data["price"], quantity)

        # 5. Execute Order in DB (Deducts stock automatically)
        order_result = self.order_service.create_order(
            patient_id=patient_id,
            product_id=product_data["product_id"],
            quantity=quantity,
            total_price=total_price
        )

        if "error" in order_result:
            return {"approved": False, "error": order_result["error"]}

        # --- STEP 6: REAL WORLD TOOL USE (Replaces Old Webhook) ---
        
        # A. Trigger Warehouse
        warehouse_res = ExternalTools.trigger_warehouse_fulfillment(
            order_id=order_result["order_id"],
            product_name=product_data["product_name"],
            quantity=quantity
        )

        # B. Send WhatsApp Confirmation
        # We assume patient_id is the mobile number based on auth logic
        msg_body = (
            f"✅ Order Confirmed!\n"
            f"Order ID: {order_result['order_id'][:8]}\n"
            f"Medicine: {product_data['product_name']} (x{quantity})\n"
            f"Total: ${total_price}\n\n"
            f"Your package has been dispatched. 🚚"
        )
        ExternalTools.send_whatsapp_message(to_mobile=str(patient_id), message_body=msg_body)

        # 7. Final Response back to Decision Agent
        return {
            "approved": True,
            "message": "Order processed successfully",
            "order": order_result,
            "fulfillment": warehouse_res
        }
    
    def __del__(self):
        # Close DB connection when agent is destroyed
        self.db.close()