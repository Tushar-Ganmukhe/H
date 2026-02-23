import pandas as pd
from langfuse import observe

HISTORY_FILE = "D:\Consumer Order History 1.xlsx"

class HistoryService:
    def __init__(self):
        self.df = pd.read_excel(HISTORY_FILE, header=4)
        self.df.columns = self.df.columns.str.strip()  # 🔥 important

    @observe(name="get_patient_history")
    def get_patient_history(self, patient_id: str):
        return self.df[self.df["Patient ID"] == patient_id].to_dict(orient="records")
