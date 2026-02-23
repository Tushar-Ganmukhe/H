from datetime import datetime, timedelta
from langfuse import observe
from app.services.history_service import HistoryService


class RefillAgent:

    def __init__(self):
        self.history_service = HistoryService()

    @observe(name="check_refills")
    def check_refills(self):

        history = self.history_service.get_all_history()
        alerts = []

        for h in history:

            # Example fields from your Excel:
            # Patient id | Purchase date | Product Name | Quantity | Dosage frequency

            purchase_date = h.get("purchase_date")
            dosage = h.get("dosage_frequency", "").lower()
            quantity = h.get("quantity", 0)

            if not purchase_date or not dosage:
                continue

            try:
                last_purchase = datetime.strptime(purchase_date, "%Y-%m-%d")
            except:
                continue

            # Only predict for daily medicines
            if "daily" in dosage:

                days_supply = int(quantity)

                next_needed = last_purchase + timedelta(days=days_supply)

                # If medicine will finish in next 3 days → alert
                if next_needed - datetime.now() <= timedelta(days=3):

                    alerts.append({
                        "patient_id": h.get("patient_id"),
                        "product_name": h.get("product_name"),
                        "expected_refill_date": next_needed.strftime("%Y-%m-%d"),
                        "message": "Patient likely needs refill soon"
                    })

        return alerts