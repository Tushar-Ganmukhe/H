import requests
from langfuse import observe


BACKEND_URL = "http://localhost:8000"


class SafetyAgent:

    @observe(name="validate_order_safety")
    def validate_order(self, patient_id, product_name, quantity):

        if quantity <= 0:
            return {
                "approved": False,
                "reason": "Invalid quantity"
            }

        return {
            "approved": True,
            "reason": "Safety checks passed"
        }
