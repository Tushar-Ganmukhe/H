import pandas as pd
from langfuse import observe
import os

# Use Raw String to handle Windows path correctly
HISTORY_FILE = "D:\Consumer Order History 1.xlsx"

class HistoryService:
    def __init__(self):
        if os.path.exists(HISTORY_FILE):
            # header=None is critical because your data starts on the first row
            self.df = pd.read_excel(HISTORY_FILE, header=None)
            print(f"📊 HistoryService: Loaded {len(self.df)} rows from Excel.")
        else:
            print(f"❌ HistoryService: File NOT found at {HISTORY_FILE}")
            self.df = pd.DataFrame()

    @observe(name="get_all_history")
    def get_all_history(self):
        """Maps specific Excel columns by index to a dictionary for the Refill Agent"""
        if self.df.empty:
            return []
            
        history_list = []
        for _, row in self.df.iterrows():
            try:
                # Map using the exact indices verified by diagnostic test
                history_list.append({
                    "patient_id": str(row[0]),          # Column A
                    "purchase_date": str(row[3]),      # Column D
                    "product_name": str(row[4]),       # Column E
                    "quantity": row[5],                # Column F
                    "dosage_frequency": str(row[7])    # Column H
                })
            except Exception:
                continue 
        return history_list

    @observe(name="get_patient_history")
    def get_patient_history(self, patient_id: str):
        all_data = self.get_all_history()
        return [h for h in all_data if h["patient_id"] == patient_id]