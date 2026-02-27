import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import observe

load_dotenv()

llm = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model="llama-3.1-8b-instant", temperature=0)

@observe(name="tier3_state_parser")
def parse_user_message(user_message: str, current_state_json: str):
    system_prompt = f"""
You are a Dialogue State Tracker for a Pharmacy.
Given the CURRENT_STATE and a NEW_MESSAGE, output a updated JSON state.

CURRENT_STATE:
{current_state_json}

INSTRUCTIONS:
1. Identify if the user provides a product_name or quantity. Update 'current_slots'.
2. If user says "Yes", "Confirm", "Book it", set intent to "CONFIRM".
3. If user describes a symptom, set intent to "SYMPTOM".
4. If user asks about a different medicine, add it to entity_stack.

OUTPUT FORMAT (Strict JSON):
{{
  "intent": "ORDER | INFO | SYMPTOM | CONFIRM | CANCEL",
  "updated_slots": {{"product_name": "string or null", "quantity": int}},
  "new_entity": "string or null",
  "response_text": "A brief acknowledgement"
}}
"""
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
    
    try:
        response = llm.invoke(messages)
        return json.loads(response.content)
    except:
        return {"intent": "UNKNOWN", "updated_slots": {}, "new_entity": None, "response_text": "I see. Tell me more."}