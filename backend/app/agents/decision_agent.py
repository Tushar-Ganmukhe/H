import json
import os
from langfuse import observe
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from app.agents.safety_agent import SafetyAgent
from app.agents.execution_agent import ExecutionAgent
from app.services.vector_store import search_by_symptom, search_product
from app.agents.memory import get_memory

class DecisionAgent:

    def __init__(self):
        self.safety_agent = SafetyAgent()
        self.execution_agent = ExecutionAgent()
        # Internal LLM instance for translation and clarification tasks
        self.translator_llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant",
            temperature=0
        )

    async def _translate_task(self, text, frequency="As directed", task_type="general"):
        """Agentic task: German-to-English Pharmacist Translator."""
        if not text or text.lower() == "nan" or text == "":
            return f"Medical records indicate usage: {frequency}. Please follow the instructions on the packaging."
        
        if task_type == "dosage":
            prompt = f"Expert Pharmacist: Convert this dosage '{frequency}' and clinical text '{text}' into clear English steps for a patient."
        else:
            prompt = f"Translate this German medical description into friendly English: {text}"
        
        try:
            response = await self.translator_llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
        except:
            return f"Usage: {frequency}. (Instruction translation unavailable)."

    @observe(name="decide_on_user_intent")
    async def decide(self, parsed_input, session_id: str, image_data: str = None):
        # 1. Access Memory State
        memory = get_memory(session_id)
        pending_verification_product = memory.get_state("pending_verification")

        # 2. Clean JSON parsing if necessary
        if isinstance(parsed_input, str):
            try:
                clean_input = parsed_input.replace("```json", "").replace("```", "").strip()
                parsed_input = json.loads(clean_input)
            except Exception:
                return {"message": "Could you please clarify the medicine name or symptom?"}

        intent = parsed_input.get("intent")
        product_name = parsed_input.get("product_name")
        quantity = parsed_input.get("quantity")
        friendly_msg = parsed_input.get("friendly_response", "")

        # --- FIX: BREAK THE PRESCRIPTION MEMORY LOCK ---
        # If user asks for a new product, forget the old prescription check.
        if product_name and pending_verification_product and product_name.lower() != pending_verification_product.lower():
            print(f"🔄 [STATE]: User changed mind. Clearing pending state for '{pending_verification_product}'")
            memory.clear_state("pending_verification")
            pending_verification_product = None # Update local variable

        # --- STATE RECOVERY LOGIC ---
        if image_data and pending_verification_product:
            print(f"🔄 [STATE]: Resuming verification for {pending_verification_product}")
            product_name = pending_verification_product
            intent = "order" 
            memory.clear_state("pending_verification")
        
        # LOG FOR TERMINAL TRACKING
        print(f"⚡ [INTENT ROUTING]: Processing '{intent}' | Product: '{product_name}'")

        # --- GLOBAL RESOLVER STEP ---
        resolved_name = product_name
        if product_name:
            resolved_name = search_product(product_name) or product_name
            print(f"🔍 [GLOBAL RESOLVER]: '{product_name}' resolved to '{resolved_name}'")

        # If we failed to find a product, but the intent needs one, fail gracefully.
        if not resolved_name and intent in ["order", "product_info", "product_description", "dosage_instruction"]:
            return {"message": f"I'm sorry, I couldn't find '{product_name}' in our inventory. Please check the spelling or ask for something else."}

        # --- INTENT: ORDER ---
        if intent == "order":
            qty = quantity or 1
            product_data = self.execution_agent.product_service.get_product_by_name(resolved_name)
            
            if not product_data:
                 return {"message": f"I'm sorry, I couldn't find '{resolved_name}' in our inventory."}

            if product_data.get("prescription_required", False):
                print(f"🔒 [GATEKEEPER]: {resolved_name} requires prescription.")
                if not image_data:
                    memory.set_state("pending_verification", resolved_name)
                    return {
                        "message": f"⚠️ **Prescription Required**\n\n**{resolved_name}** is a restricted medicine. Please click the **paperclip icon 📎** to upload a photo of your doctor's prescription so I can verify it."
                    }
                
                verification = await self.safety_agent.verify_prescription(image_data, resolved_name)
                
                if not verification.get("approved"):
                    memory.set_state("pending_verification", resolved_name)
                    return {
                        "message": f"❌ **Verification Failed**\n\nI couldn't approve this order. Reason: {verification.get('reason')}. Please upload a clear image of a valid prescription."
                    }
                
                print(f"✅ [GATEKEEPER]: Prescription Verified for {resolved_name}.")

            safety = self.safety_agent.validate_order(patient_id=session_id, product_name=resolved_name, quantity=qty)
            if not safety["approved"]:
                return {"message": f"❌ **Safety Block**: {safety['reason']}"}
            
            res = await self.execution_agent.execute_order(patient_id=session_id, product_name=resolved_name, quantity=qty)
            if res.get("approved"):
                order_id = res['order']['order_id']
                total = res['order']['total_price']
                return {
                    "message": f"✅ **Order Confirmed**\n\nSuccessfully placed your order for **{qty}x {resolved_name}**.\n\n**Total:** ${total}\n**Order ID:** `{order_id}`"
                }
            return {"message": f"❌ **Fulfillment Error**: {res.get('error')}"}

        # --- INTENT: REORDER LAST ---
        if intent == "reorder_last":
            last_order = self.execution_agent.order_service.get_last_order(session_id)
            if last_order:
                return {
                    "message": f"🔄 **Fast Reorder**\n\nI found your last order: **{last_order.product_name}** (Qty: {last_order.quantity}). Would you like me to place the same order for you now? reply with order it "
                }
            return {"message": "No previous orders found in your account history."}

        # --- INTENT: SYMPTOM RECOMMENDATION ---
        if intent == "symptom_recommendation":
            symptom = parsed_input.get("symptom") or "your symptoms"
            recommended = search_by_symptom(symptom)
            if recommended and recommended != "None":
                product = self.execution_agent.product_service.get_product_by_name(recommended)
                price = product['price'] if product else "N/A"
                return {"message": f"👨‍⚕️ **Recommendation**\n\nFor '{symptom}', I suggest **{recommended}**. It costs **${price}**. Shall I explain how it works?"}
            return {"message": f"I couldn't find a matching medicine for '{symptom}'. Please consult our pharmacist."}

        # --- INTENT: DOSAGE INSTRUCTION ---
        if intent == "dosage_instruction":
            product_data = self.execution_agent.product_service.get_product_by_name(resolved_name)
            if product_data:
                instruction = await self._translate_task(product_data.get("description", ""), product_data.get("dosage_frequency", "As directed"), "dosage")
                return {"message": f"⏲️ **Dosage for {resolved_name}**\n\n{instruction}"}
            return {"message": f"I couldn't retrieve dosage instructions for {resolved_name}."}

        # --- INTENT: PRODUCT DESCRIPTION ---
        if intent == "product_description":
            product_data = self.execution_agent.product_service.get_product_by_name(resolved_name)
            if product_data:
                english_desc = await self._translate_task(product_data.get("description", ""))
                return {"message": f"📖 **Medicine Details: {resolved_name}**\n\n{english_desc}"}
            return {"message": f"I don't have a medical description for {resolved_name}."}

        # --- INTENT: PRODUCT INFO ---
        if intent == "product_info":
            product_data = self.execution_agent.product_service.get_product_by_name(resolved_name)
            if product_data:
                return {"message": f"🔍 **Price Check**\n\n**{resolved_name}** is currently available at **${product_data['price']}** per unit."}
            return {"message": f"I couldn't find **{resolved_name}** in our current inventory."}

        return {"message": friendly_msg or "How else can I help you today?"}