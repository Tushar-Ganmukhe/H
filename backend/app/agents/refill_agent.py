import pandas as pd
from datetime import datetime, timedelta
from langfuse import observe
from app.services.history_service import HistoryService
from app.core.database import SessionLocal
from app.core.models import Order

class RefillAgent:
    def __init__(self):
        self.history_service = HistoryService()
        self.db = SessionLocal()

    def parse_dosage(self, dosage_str):
        ds = str(dosage_str).lower()
        if "three times daily" in ds: return 3
        if "twice daily" in ds: return 2
        if "once daily" in ds or "daily" in ds: return 1
        return 0 

    @observe(name="check_refills")
    def check_refills(self):
        # 1. Fetch from Excel (History)
        combined_data = self.history_service.get_all_history()
        
        # 2. Fetch from SQLite (Live Orders)
        try:
            live_orders = self.db.query(Order).all()
            for o in live_orders:
                combined_data.append({
                    "patient_id": o.patient_id,
                    "purchase_date": o.created_at,
                    "product_name": o.product_name,
                    "quantity": o.quantity,
                    "dosage_frequency": "once daily" 
                })
        finally:
            self.db.close()

        alerts = []
        today = datetime.now()

        for h in combined_data:
            try:
                p_date = pd.to_datetime(h.get("purchase_date"))
                qty = h.get("quantity", 0)
                daily_qty = self.parse_dosage(h.get("dosage_frequency"))
                
                if daily_qty > 0 and qty > 0:
                    days_supply = int(qty) / daily_qty
                    next_needed = p_date + timedelta(days=days_supply)
                    days_remaining = (next_needed - today).days

                    if days_remaining <= 3:
                        alerts.append({
                            "patient_id": h.get("patient_id"),
                            "product_name": h.get("product_name"),
                            "expected_refill_date": next_needed.strftime("%Y-%m-%d"),
                            "message": "🚨 Critical Overdue" if days_remaining < 0 else "⚠️ Refill Due Soon"
                        })
            except: continue

        # Deduplicate alerts based on patient + product
        unique_alerts = { (a['patient_id'], a['product_name']): a for a in alerts }.values()
        return sorted(list(unique_alerts), key=lambda x: x['expected_refill_date'], reverse=True)