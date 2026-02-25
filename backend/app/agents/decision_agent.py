import json
import os
from langfuse import observe
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.safety_agent import SafetyAgent
from app.agents.execution_agent import ExecutionAgent
from app.agents.guardrail import validate_llm_output
from app.services.vector_store import search_by_symptom, search_product

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
    async def decide(self, parsed_input, session_id: str):
        # 1. Clean JSON parsing
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

        # LOG FOR TERMINAL TRACKING
        print(f"⚡ [INTENT ROUTING]: Processing '{intent}' | Product: '{product_name}'")

        # --- GLOBAL RESOLVER STEP (FIXED ATTRIBUTE ERROR) ---
        resolved_name = product_name
        if product_name:
            resolved_name = search_product(product_name) or product_name
            print(f"🔍 [GLOBAL RESOLVER]: '{product_name}' resolved to '{resolved_name}'")

        if not resolved_name and intent != "reorder_last" and intent != "symptom_recommendation":
            return {"message": friendly_msg or "I'm ready. Which medicine are we discussing today?"}

        # --- INTENT: ORDER ---
        if intent == "order":
            qty = quantity or 1
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
                return {"message": f"👨‍⚕️ **Recommendation**\n\nFor '{symptom}', I suggest **{recommended}**. It costs **${product['price']}**. Shall I explain how it works?"}
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