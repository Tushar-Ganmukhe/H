import httpx
from langfuse import observe
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.vector_store import search_product

# Configuration
WAREHOUSE_WEBHOOK = "http://localhost:9000/fulfill"  # Mock webhook

@observe(name="pricing_calculation")
def calculate_price(price, qty):
    # Ensure inputs are numbers to avoid errors
    try:
        return round(float(price) * int(qty), 2)
    except:
        return 0

class ExecutionAgent:

    def __init__(self):
        self.order_service = OrderService()
        self.product_service = ProductService()

    @observe(name="order_execution")
    async def execute_order(self, patient_id: int, product_name: str, quantity: int):
        
        # 1️⃣ Validation: Ensure product name isn't empty
        if not product_name or str(product_name).strip() == "":
             return {
                "approved": False,
                "error": "I couldn't identify the medicine name. Please specify which medicine you need."
            }

        # 2️⃣ Resolve product name using vector search (Fuzzy match)
        # This helps match "Paracetamol" with the long name in your Excel
        resolved_name = search_product(product_name) or product_name
        
        # 3️⃣ Fetch Product Details from Excel
        product = self.product_service.get_product_by_name(resolved_name)

        if not product:
            return {
                "approved": False,
                "error": f"Product '{product_name}' was not found in our inventory."
            }

        # 4️⃣ Safe price and ID extraction
        # product_service already mapped 'price rec' to 'price' for us
        price_per_unit = product.get("price", 0)
        product_id = product.get("product_id", "UNKNOWN")

        total_price = calculate_price(price_per_unit, quantity)

        # 5️⃣ Create Order in the local list
        order = self.order_service.create_order(
            patient_id=patient_id,
            product_id=product_id,
            quantity=quantity,
            total_price=total_price
        )

        # 6️⃣ Trigger Warehouse Webhook (Mock Fulfillment)
        # We add a TIMEOUT so if the warehouse is offline, the chat doesn't get stuck!
        webhook_payload = {
            "order_id": order["order_id"],
            "product": product.get("product_name"),
            "quantity": quantity,
            "total_price": total_price
        }

        try:
            async with httpx.AsyncClient() as client:
               # ✅ Added timeout=1.0 to prevent infinite loading
               await client.post(WAREHOUSE_WEBHOOK, json=webhook_payload, timeout=1.0)
        except Exception as e:
            # If warehouse is offline, we still finish the order logic
            print(f"⚠️ Webhook skipped (Warehouse offline): {e}")

        # 7️⃣ Return Response to Decision Agent
        return {
            "approved": True,
            "message": f"Order placed successfully!",
            "order": order
        }