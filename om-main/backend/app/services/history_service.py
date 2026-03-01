import pandas as pd
from langfuse import observe
import pandas as pd
from langfuse import observe
from app.services.order_service import ORDERS # ✅ Import the newly created orders

HISTORY_FILE = "D:\Downlod\Consumer History 1.xlsx"

class HistoryService:
    def __init__(self):
        self.df = pd.read_excel(HISTORY_FILE, header=4)
        self.df.columns = self.df.columns.str.strip()  # 🔥 important
        # Ensure Patient ID is a string for safe comparison
        if "Patient ID" in self.df.columns:
            self.df["Patient ID"] = self.df["Patient ID"].astype(str)

    @observe(name="get_patient_history")
    def get_patient_history(self, patient_id: str):
        # 1. Get old history from the Excel file
        excel_history = self.df[self.df["Patient ID"] == str(patient_id)].to_dict(orient="records")
        
        # 2. Get new history from the active session (ORDERS list)
        new_orders_formatted = []
        for o in ORDERS:
            if str(o.get("patient_id")) == str(patient_id):
                new_orders_formatted.append({
                    "Product Name": o.get("product_name") or f"Product ID: {o.get('product_id')}",
                    "Quantity": o.get("quantity"),
                    "Purchase date": o.get("created_at").strftime("%Y-%m-%d") if o.get("created_at") else "Just now",
                    "Dosage frequency": "New Order (Pending)"
                })
                
        # 3. Combine them! Show the newest orders at the top.
        return new_orders_formatted + excel_history