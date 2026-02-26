import os
import json
from langfuse import observe
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

class SafetyAgent:

    def __init__(self):
        # Vision Model for Prescription Verification
        self.vision_llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.2-11b-vision-preview",
            temperature=0
        )

    @observe(name="verify_prescription_image")
    async def verify_prescription(self, image_b64: str, product_name: str):
        """
        Uses Llama-3.2 Vision to verify if the uploaded image is a valid prescription
        and if it matches the requested medicine.
        """
        if not image_b64:
            return {"approved": False, "reason": "No image data received."}

        # Ensure base64 header is present for the API
        if "," in image_b64:
            image_data = image_b64.split(",")[1]
            image_url = f"data:image/jpeg;base64,{image_data}"
        else:
            image_url = f"data:image/jpeg;base64,{image_b64}"

        prompt = f"""
        You are a strict Pharmacist Regulatory Bot.
        Analyze this image. 
        1. Is it a valid medical prescription (doctor's note, hospital discharge, or script)? 
        2. Does it mention the medicine '{product_name}' (or a similar generic name)?
        
        Return ONLY valid JSON:
        {{
            "approved": boolean, 
            "reason": "short explanation"
        }}
        """

        msg = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
                },
            ]
        )

        try:
            response = await self.vision_llm.ainvoke([msg])
            content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"Vision AI Error: {e}")
            return {
                "approved": False, 
                "reason": "I could not analyze the image clearly. Please upload a clearer photo."
            }

    @observe(name="validate_order_safety")
    def validate_order(self, patient_id, product_name, quantity):
        """Basic logic safety checks (Quantity limits, etc.)"""
        
        if quantity <= 0:
            return {
                "approved": False,
                "reason": "Invalid quantity"
            }
        
        # In a real app, you might check drug interactions here too
        
        return {
            "approved": True,
            "reason": "Safety checks passed"
        }