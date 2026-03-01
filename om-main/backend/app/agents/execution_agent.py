import os
import re
import httpx
from langfuse import observe

from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.symptom_matcher import SymptomMatcher
from app.services.user_service import UserService
from app.services.vector_store import search_product

try:
    from twilio.rest import Client
except ImportError:
    Client = None


WAREHOUSE_WEBHOOK = "http://localhost:9000/fulfill"


def send_notification(phone: str, message: str):
    """Send a WhatsApp notification via Twilio if credentials are set."""
    if not Client:
        print("Twilio library not installed. Run: pip install twilio")
        return
        
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_num = os.getenv("TWILIO_WHATSAPP_FROM")
    
    if not sid or not token or not from_num or not phone:
        print("Missing Twilio credentials or phone number in .env.")
        return
        
    # FORCE CORRECT PHONE FORMATTING
    # 1. Remove any spaces, dashes, or weird characters
    clean_phone = re.sub(r'[^\d+]', '', str(phone))
    
    # 2. If it's exactly 10 digits without a '+', force +91 (India)
    if len(clean_phone) == 10 and clean_phone.isdigit():
        formatted_phone = f"+91{clean_phone}"
    elif not clean_phone.startswith('+'):
        formatted_phone = f"+{clean_phone}"
    else:
        formatted_phone = clean_phone

    # Ensure from_num has the whatsapp: prefix
    if not from_num.startswith("whatsapp:"):
        from_num = f"whatsapp:{from_num}"

    try:
        client = Client(sid, token)
        client.messages.create(
            body=message, 
            from_=from_num, 
            to=f"whatsapp:{formatted_phone}"
        )
        print(f"✅ WhatsApp message successfully sent to {formatted_phone}")
    except Exception as e:
        print(f"❌ Failed to send WhatsApp notification: {e}")


@observe(name="pricing_calculation")
def calculate_price(price, qty):
    try:
        return round(float(price) * int(qty), 2)
    except Exception:
        return 0


class ExecutionAgent:
    def __init__(self):
        self.order_service = OrderService()
        self.product_service = ProductService()
        self.symptom_matcher = SymptomMatcher()

    @observe(name="order_execution")
    async def execute_order(self, patient_id: int, product_name: str, quantity: int):
        if not product_name or str(product_name).strip() == "":
            return {
                "approved": False,
                "error": "I couldn't identify the medicine name. Please specify which medicine you need.",
            }

        # Ensure we always check latest stock from disk.
        self.product_service.reload()

        resolved_name = search_product(product_name) or product_name
        product = self.product_service.get_product_by_name(resolved_name)

        if not product:
            return {
                "approved": False,
                "error": f"Product '{product_name}' was not found in our inventory.",
            }

        canonical_name = product.get("product_name", resolved_name)
        available, message = self.product_service.check_stock_availability(canonical_name, quantity)
        if not available:
            return {
                "approved": False,
                "error": f"**Insufficient Stock**: {message}",
            }

        price_per_unit = product.get("price", 0)
        product_id = product.get("product_id", "UNKNOWN")
        total_price = calculate_price(price_per_unit, quantity)

        # Create one order record only.
        order = self.order_service.create_order(
            patient_id=patient_id,
            product_id=product_id,
            quantity=quantity,
            total_price=total_price,
            product_name=product.get("product_name"),
        )

        webhook_payload = {
            "order_id": order["order_id"],
            "product": product.get("product_name"),
            "quantity": quantity,
            "total_price": total_price,
        }

        try:
            async with httpx.AsyncClient() as client:
                await client.post(WAREHOUSE_WEBHOOK, json=webhook_payload, timeout=1.0)
        except Exception:
            print("WARNING: Webhook skipped (Warehouse offline)")

        self.product_service.reduce_stock(canonical_name, quantity)
        updated = self.product_service.get_product_by_name(canonical_name)
        rem_stock = updated.get("stock") if updated else None

        notification_sent = False
        phone = None
        try:
            user = UserService.get_user(patient_id)
            phone = user.get("phone") if user else None
            if phone:
                send_notification(
                    phone,
                    f"Your order {order['order_id']} for {quantity}x {product.get('product_name')} has been placed successfully."
                )
                notification_sent = True
        except Exception as e:
            print(f"Notification error: {e}")

        return {
            "approved": True,
            "message": "Order placed successfully!",
            "order": order,
            "remaining_stock": rem_stock,
            "notification_sent": notification_sent,
            "notification_phone": phone if notification_sent else None,
        }

    @observe(name="recommend_products")
    def recommend_products(self, symptom: str):
        """
        Use advanced symptom matching to find best products.
        Returns 1-3 products that match the symptom with translation and scoring.
        """
        try:
            self.product_service.reload()
            all_products = self.product_service.get_all_products()

            if not all_products:
                return {"found": False, "matches": []}

            result = self.symptom_matcher.match_symptom_to_products(
                symptom=symptom,
                products=all_products,
                threshold=0.5,
            )

            if result["total_matches"] == 0:
                return {
                    "found": False,
                    "matches": [],
                    "message": self.symptom_matcher.generate_response(symptom, []),
                }

            top_matches = result["matches"][:3]
            return {
                "found": True,
                "matches": top_matches,
                "symptom_categories": result["symptom_categories"],
                "total_matches": result["total_matches"],
            }
        except Exception as e:
            print(f"Error in recommend_products: {e}")
            return {"found": False, "matches": []}

    @observe(name="get_product_info")
    def get_product_details(self, product_name: str):
        if not product_name or str(product_name).strip() == "":
            return {"found": False, "error": "Please specify which medicine you need."}

        self.product_service.reload()
        resolved_name = search_product(product_name) or product_name
        product = self.product_service.get_product_by_name(resolved_name)

        if not product:
            return {"found": False, "error": f"Product '{product_name}' was not found."}

        return {"found": True, "product": product}