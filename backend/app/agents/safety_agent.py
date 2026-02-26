import os
import json
import google.generativeai as genai
from langfuse import observe
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

class SafetyAgent:

    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        # 1. Dynamically find the best available Gemini Vision model
        self.vision_model_name = self._get_available_vision_model()
        print(f"✅ [SAFETY AGENT]: Initialized with dynamic vision model: {self.vision_model_name}")

        # 2. Initialize LangChain with the dynamically found model
        self.vision_llm = ChatGoogleGenerativeAI(
            model=self.vision_model_name,
            temperature=0,
            google_api_key=self.google_api_key
        )

    def _get_available_vision_model(self) -> str:
        """
        Scans Google AI Studio for available models and selects the best one 
        to prevent 'Model Not Found' errors.
        """
        try:
            genai.configure(api_key=self.google_api_key)
            # Fetch all models that support content generation
            available_models =[
                m.name for m in genai.list_models() 
                if 'generateContent' in m.supported_generation_methods
            ]
            
            # List of preferred vision-capable models (from newest/fastest to oldest)
            preferences =[
                'models/gemini-2.5-flash',
                'models/gemini-2.0-flash', 
                'models/gemini-1.5-flash', 
                'models/gemini-1.5-pro'
            ]
            
            # Check preferences against available models
            for pref in preferences:
                if pref in available_models:
                    return pref
                    
            # Fallback: Just return the first available gemini model
            for model in available_models:
                if 'gemini' in model:
                    return model
                    
        except Exception as e:
            print(f"⚠️ Dynamic model fetch failed: {e}. Defaulting to gemini-1.5-flash")
            
        # Absolute fallback if API listing fails
        return "gemini-1.5-flash"

    @observe(name="verify_prescription_image")
    async def verify_prescription(self, image_b64: str, product_name: str):
        """
        Uses dynamically selected Google Gemini Vision to verify if the uploaded image looks like a valid prescription.
        """
        if not image_b64:
            return {"approved": False, "reason": "No image data received."}

        # Ensure base64 header is present for the API
        if "," in image_b64:
            image_data = image_b64.split(",")[1]
            image_url = f"data:image/jpeg;base64,{image_data}"
        else:
            image_url = f"data:image/jpeg;base64,{image_b64}"

        # Prompt for image verification
        prompt = f"""
        You are a Pharmacy Assistant verifying documents.
        Analyze this image. 
        Does it look like a medical prescription, doctor's note, clinic receipt, or medical document?
        (Look for handwriting, medical symbols, RX signs, clinic letterheads, or lists of medicines).
        
        You DO NOT need to strictly verify if the exact text '{product_name}' is written. 
        As long as it appears to be a genuine medical document/prescription, approve it.
        If it is obviously a picture of a cat, a car, a random selfie, or blank paper, reject it.
        
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
            
            # Aggressively clean the response to ensure it parses as JSON
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            return json.loads(content)
        except Exception as e:
            print(f"Vision AI Error: {e}")
            return {
                "approved": False, 
                "reason": "I could not analyze the image clearly. Please try uploading a clearer photo."
            }

    @observe(name="validate_order_safety")
    def validate_order(self, patient_id, product_name, quantity):
        """Basic logic safety checks (Quantity limits, etc.)"""
        
        if quantity <= 0:
            return {
                "approved": False,
                "reason": "Invalid quantity"
            }
        
        return {
            "approved": True,
            "reason": "Safety checks passed"
        }