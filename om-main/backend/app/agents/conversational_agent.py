from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import observe, get_client
import os


llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0
)


SYSTEM_PROMPT = """
You are an expert Pharmacy Assistant named "PharmaBot". You are helpful, friendly, and professional.

You MUST output ONLY valid JSON.

Schema:
{
  "intent": "order | product_info | general_chat",
  "product_name": string | null,
   "symptom": string | null,
  "quantity": integer | null,
  "missing": "product_name" | "quantity" | null,
  "friendly_response": string
}

Rules:
1. If the user wants to buy/order/purchase -> intent="order".
2. If the user asks for PRICE, AVAILABILITY, DESCRIPTION, or specific MEDICINE INFO -> intent="product_info".
3. If the user says "Hi", "Hello", "Thanks", "Bye", or asks general questions (e.g., "How are you?", "What can you do?") -> intent="general_chat".
4. IMPORTANT CONTEXT: You will receive the Conversation History. If the user's latest message is just a number (e.g., "2", "two") or a short confirmation, INHERIT the "product_name" and "intent" from the History!
5. In 'friendly_response': 
   - For 'order'/'product_info': Talk like a helpful assistant (e.g., "I'll check that for you.").
   - For 'general_chat': Respond naturally to the user's input (e.g., "I'm doing great! How can I help you with your health today?").
6. If user describes a FEELING, PAIN, or CONDITION (e.g., "I feel warm", "headache", "flu", "stomach pain") -> intent="symptom_check". Extract the condition into "symptom".
7. If general chat -> intent="general_chat".
8. IMPORTANT: Inherit context from history if the user replies with just a number.

CRITICAL RULE: 
If the user mentions a symptom like "Exhaustion" or "Fatigue" and DOES NOT mention a product name, you MUST set intent="symptom_check". Do NOT ask the user for a product name; suggest one instead

"""
@observe(name="parse_user_message")
def parse_user_message(user_message: str):
    """Parse user message and extract intent, product, quantity using LLM."""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]

    # Get Langfuse client for LLM tracing
    client = get_client()
    langchain_handler = client.get_trace_handler() if hasattr(client, 'get_trace_handler') else None
    if langchain_handler:
        response = llm.invoke(messages, config={"callbacks": [langchain_handler]})
    else:
        response = llm.invoke(messages)

    return response.content 