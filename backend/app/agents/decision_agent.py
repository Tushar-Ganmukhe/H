import json
from langfuse import observe
from app.agents.safety_agent import SafetyAgent
from app.agents.execution_agent import ExecutionAgent
from app.agents.guardrail import validate_llm_output

class DecisionAgent:

    def __init__(self):
        self.safety_agent = SafetyAgent()
        self.execution_agent = ExecutionAgent()

    @observe(name="decide_on_user_intent")
    async def decide(self, parsed_input, session_id: str): # FIX: Added session_id parameter
        # 1. Handle string input from LLM and clean JSON code blocks
        if isinstance(parsed_input, str):
            try:
                # Remove markdown backticks if the LLM included them
                clean_input = parsed_input.replace("```json", "").replace("```", "").strip()
                parsed_input = json.loads(clean_input)
            except Exception:
                return {"message": "I'm sorry, I'm having trouble processing that request. Could you please specify the medicine name and quantity?"}

        # Extract core fields from LLM extraction
        intent = parsed_input.get("intent")
        product_name = parsed_input.get("product_name")
        quantity = parsed_input.get("quantity")
        friendly_msg = parsed_input.get("friendly_response", "")

        # 2. Handle GREETINGS or GENERAL QUESTIONS
        if intent == "unknown" or not intent:
            return {"message": friendly_msg or "Hello! I'm your Pharmacy Assistant. How can I help you with your medications today?"}

        # 3. Validation: If we are missing a product name for a specific request
        if not product_name:
            return {"message": friendly_msg or "Which medicine are you inquiring about?"}

        # ---------------------------------------------------------
        # CASE A: PRODUCT INFO / PRICE CHECK
        # ---------------------------------------------------------
        if intent == "product_info":
            # Call execution agent with quantity 1 just to get price data
            data = await self.execution_agent.execute_order(
                patient_id=session_id, # FIX: Replaced hardcoded 1
                product_name=product_name,
                quantity=1
            )

            if not data.get("approved"):
                return {"message": f"I checked our inventory, but I couldn't find **{product_name}**. Please double-check the spelling!"}

            # Get the price from the 'order' object (calculated from 'price rec' in Excel)
            price = data.get("order", {}).get("total_price", 0)
            
            return {
                "message": f"🔍 **Medicine Information**\n\nThe current price for **{product_name}** is **${price}** per unit.\n\nWould you like me to place an order for you?"
            }

        # ---------------------------------------------------------
        # CASE B: PLACING AN ORDER
        # ---------------------------------------------------------
        if intent == "order":
            # Check if quantity is missing
            if parsed_input.get("missing") == "quantity" or not quantity:
                return {"message": f"I've found **{product_name}** in our system. How many units or strips would you like to order?"}

            # Guardrail Validation (Check for reasonable limits)
            valid, reason = validate_llm_output(parsed_input)
            if not valid:
                return {"message": f"⚠️ **Order Notice**: {reason}"}

            # Safety Agent Validation
            safety = self.safety_agent.validate_order(
                patient_id=session_id, # FIX: Replaced hardcoded 1
                product_name=product_name,
                quantity=quantity
            )

            if not safety["approved"]:
                return {"message": f"❌ **Safety Check Failed**: {safety['reason']}"}

            # Final Execution (Calculate price, create ID, trigger webhook)
            execution_result = await self.execution_agent.execute_order(
                patient_id=session_id, # FIX: Replaced hardcoded 1
                product_name=product_name,
                quantity=quantity
            )

            if execution_result.get("approved"):
                total = execution_result['order']['total_price']
                order_id = execution_result['order']['order_id']
                return {
                    "message": f"✅ **Order Confirmed**\n\nI have successfully placed your order for **{quantity}x {product_name}**.\n\n**Total:** ${total}\n**Order ID:** `{order_id}`\n\nYour medicine will be prepared for delivery shortly."
                }
            else:
                return {"message": f"❌ **Fulfillment Error**: {execution_result.get('error', 'I could not process the order at this time.')}"}

        # Fallback for any other cases
        return {"message": friendly_msg or "I'm here to help with your pharmacy needs. You can ask me for medicine prices or to place an order."}