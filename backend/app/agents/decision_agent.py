import json
import os
from dotenv import load_dotenv
from app.agents.memory import memory_store
from app.agents.execution_agent import ExecutionAgent
from app.agents.safety_agent import SafetyAgent
from app.services.vector_store import search_product
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import observe

load_dotenv()

class DecisionAgent:
    def __init__(self):
        self.executor = ExecutionAgent()
        self.safety = SafetyAgent()
        self.llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"), 
            model="llama-3.1-8b-instant", 
            temperature=0
        )

    async def _reason_with_german_context(self, user_query, product_data, target_lang="en"):
        prompt = f"""
        User Query: {user_query}
        Medicine Data: {product_data['product_name']} | Description: {product_data['description']}
        Explain in {target_lang} if this matches. Return JSON: {{"match": bool, "explanation": "str"}}
        """
        try:
            res = await self.llm.ainvoke([SystemMessage(content="You are a pharmacist."), HumanMessage(content=prompt)])
            content = res.content.strip().replace("```json", "").replace("```", "")
            return json.loads(content)
        except:
             return {"match": True, "explanation": f"I found {product_data['product_name']}."}

    @observe(name="tier3_decision_with_vision")
    async def decide(self, nlp_output: dict, session_id: str, user_lang="en", image_data: str = None):
        mem = memory_store.get_state(session_id)
        intent = nlp_output.get("intent")
        slots = nlp_output.get("updated_slots", {})
        
        # ---------------------------------------------------------
        # 1. INTELLIGENT SLOT RESOLUTION (THE FIX)
        # ---------------------------------------------------------
        if slots.get("product_name"):
            resolved_name = search_product(slots["product_name"])
            
            # CRITICAL FIX: Only reset safety if the product implies a CONTEXT SWITCH
            # If LLM repeats the SAME product name during "Confirm", do NOT reset.
            if resolved_name != mem.current_slots["product_name"]:
                mem.prescription_verified = False 
                mem.transaction_state = "IDLE" 
            
            # Update the slot to the resolved name
            mem.current_slots["product_name"] = resolved_name
            memory_store.update_entity_stack(session_id, resolved_name)

        if slots.get("quantity"):
            mem.current_slots["quantity"] = slots["quantity"]

        # Handle Explicit Cancel
        if intent == "CANCEL":
            memory_store.clear_slots(session_id)
            return {"message": "Okay, I've cancelled that. How else can I help?"}

        # ---------------------------------------------------------
        # 2. VISION SAFETY CHECK 
        # ---------------------------------------------------------
        if mem.transaction_state == "AWAITING_PRESCRIPTION":
            # If user sent an image, process it
            if image_data:
                verification = await self.safety.verify_prescription(image_data, mem.current_slots["product_name"])
                
                if verification["approved"]:
                    mem.prescription_verified = True
                    mem.transaction_state = "PENDING_CONFIRMATION"
                    return {"message": f"✅ Prescription verified! {verification['reason']}\n\nProceed with order for {mem.current_slots['quantity']}x {mem.current_slots['product_name']}?"}
                else:
                    return {"message": f"❌ Prescription Rejected: {verification['reason']}\n\nPlease upload a valid medical document."}
            
            # If NO image and NO new product mentioned, stay stuck
            return {"message": f"⚠️ **{mem.current_slots['product_name']}** requires a prescription. Please upload a photo before we proceed, or ask for a different medicine."}

        # ---------------------------------------------------------
        # 3. ORDER LOGIC (Rx Gatekeeper)
        # ---------------------------------------------------------
        if intent in ["ORDER", "CONFIRM"] and mem.current_slots["product_name"]:
            # Fetch Product Data
            prod_data = self.executor.products.get_product_by_name(mem.current_slots["product_name"])
            
            if not prod_data:
                return {"message": "I couldn't find that medicine in our database."}

            # CHECK: Rx Requirement from Admin Portal Data
            # Only trigger if NOT already verified
            if prod_data.get("prescription_required") and not mem.prescription_verified:
                mem.transaction_state = "AWAITING_PRESCRIPTION"
                return {"message": f"⚠️ **{prod_data['product_name']}** requires a valid prescription. Please click the paperclip icon 📎 to upload a photo."}

            # Prepare Quote
            quote = self.executor.prepare_order(mem.current_slots["product_name"], mem.current_slots["quantity"])
            
            if quote["success"]:
                # If "CONFIRM" was said (State is PENDING or Intent is CONFIRM)
                if intent == "CONFIRM" or mem.transaction_state == "PENDING_CONFIRMATION":
                    await self.executor.commit_order(session_id, quote["product_id"], mem.current_slots["quantity"], quote["total"])
                    memory_store.clear_slots(session_id)
                    
                    success_msg = "✅ Order placed successfully! Your prescription has been archived."
                    if user_lang == "hi": success_msg = "✅ ऑर्डर सफलतापूर्वक दिया गया!"
                    return {"message": success_msg}
                
                # Otherwise, show quote and wait for specific confirmation
                mem.transaction_state = "PENDING_CONFIRMATION"
                return {"message": quote["msg"]}
            else:
                return {"message": f"❌ {quote.get('error')}"}

        # 4. Standard Symptoms / Info
        if intent == "SYMPTOM":
            suggested = nlp_output.get("new_entity") or nlp_output.get("response_text")
            potential_match = search_product(suggested)
            
            if potential_match:
                prod_data = self.executor.products.get_product_by_name(potential_match)
                reasoning = await self._reason_with_german_context(nlp_output.get("response_text"), prod_data, user_lang)
                
                # Context Switch implicit here too:
                if potential_match != mem.current_slots["product_name"]:
                    mem.prescription_verified = False # Reset if different
                    mem.transaction_state = "IDLE"

                mem.current_slots["product_name"] = potential_match
                mem.transaction_state = "RECOMMENDING"
                
                return {"message": f"👨‍⚕️ {reasoning['explanation']}\n\nWould you like to order it?"}

        return {"message": nlp_output.get("response_text", "How can I help you?")}