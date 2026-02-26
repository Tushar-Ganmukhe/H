import os
from langfuse import observe
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
# If these are missing in .env, the system will use "Mock Mode" (Print to console)
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_WHATSAPP_FROM") # e.g., 'whatsapp:+14155238886'

class ExternalTools:
    
    @staticmethod
    @observe(name="tool_warehouse_fulfillment")
    def trigger_warehouse_fulfillment(order_id: str, product_name: str, quantity: int, address: str = "Standard Delivery"):
        """
        Simulates sending a request to a physical warehouse system.
        """
        print(f"\n🚚 [WAREHOUSE WEBHOOK]: Dispatching Order #{order_id}")
        print(f"📦 Product: {product_name} | Qty: {quantity}")
        print(f"📍 Address: {address}")
        
        # In a real scenario, this would be requests.post('https://warehouse-api.com/ship', json=...)
        return {"status": "dispatched", "tracking_id": f"TRK-{order_id[:8]}"}

    @staticmethod
    @observe(name="tool_send_whatsapp")
    def send_whatsapp_message(to_mobile: str, message_body: str):
        """
        Sends a WhatsApp message via Twilio. 
        Falls back to Console Print if credentials are missing (Stability Guarantee).
        """
        # 1. Sanitize Mobile Number
        if not to_mobile.startswith("+"):
            # Assume India if no country code, otherwise adjust as needed
            to_mobile = f"+91{to_mobile}" 
        
        formatted_to = f"whatsapp:{to_mobile}"

        print(f"\n💬 [NOTIFICATION]: Attempting to send WhatsApp to {to_mobile}")
        print(f"📝 Message: {message_body}")

        # 2. Check for Credentials (MOCK MODE vs REAL MODE)
        if not TWILIO_SID or not TWILIO_TOKEN or not TWILIO_FROM:
            print("⚠️ [MOCK MODE]: Twilio credentials not found. Message printed to console only.")
            return {"status": "success", "mode": "mock", "sid": "mock-sid-123"}

        # 3. Real Execution
        try:
            client = Client(TWILIO_SID, TWILIO_TOKEN)
            message = client.messages.create(
                from_=TWILIO_FROM,
                body=message_body,
                to=formatted_to
            )
            print(f"✅ [TWILIO SUCCESS]: SID {message.sid}")
            return {"status": "success", "mode": "live", "sid": message.sid}
            
        except Exception as e:
            print(f"❌ [TWILIO ERROR]: {str(e)}")
            # Return success anyway so the UI doesn't break during demo
            return {"status": "error", "error": str(e)}

    @staticmethod
    @observe(name="tool_send_email")
    def send_email_message(to_email: str, subject: str, body: str):
        """
        Mock Email Sender (Email is complex to set up in hackathons due to spam filters).
        """
        print(f"\n📧 [EMAIL MOCK]: Sending to {to_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        return {"status": "sent", "mode": "mock"}