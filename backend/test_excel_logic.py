import pandas as pd
from datetime import datetime, timedelta
import os

# 1. PATH CHECK
FILE_PATH = r"D:\Consumer Order History 1.xlsx"

def diagnostic_test():
    print("--- 🔍 STARTING EXCEL DIAGNOSTIC ---")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ ERROR: File not found at {FILE_PATH}")
        return

    try:
        # 2. READ CHECK (Using header=None as seen in your screenshot)
        df = pd.read_excel(FILE_PATH, header=None)
        print(f"✅ SUCCESS: Read Excel. Found {len(df)} rows.")
        
        # 3. SAMPLE ROW CHECK
        first_row = df.iloc[0]
        print("\n--- 📝 DATA EXTRACTION TEST (ROW 1) ---")
        print(f"Col A (Patient ID): {first_row[0]}")
        print(f"Col D (Purchase Date): {first_row[3]} | Type: {type(first_row[3])}")
        print(f"Col E (Product Name): {first_row[4]}")
        print(f"Col F (Quantity): {first_row[5]}")
        print(f"Col H (Dosage): {first_row[7]}")

        # 4. REFILL CALCULATION TEST
        print("\n--- 🤖 REFILL LOGIC TEST ---")
        today = datetime.now()
        
        for index, row in df.iterrows():
            # Basic mapping
            p_id = str(row[0])
            p_date = row[3]
            p_name = str(row[4])
            qty = row[5]
            dosage = str(row[7]).lower()

            # Skip header or empty
            if p_id == "nan" or p_name == "nan": continue

            # Convert Date
            try:
                # If it's already a datetime from pandas
                last_purchase = pd.to_datetime(p_date)
            except:
                print(f"⚠️ Failed to parse date for {p_id}")
                continue

            # Dosage Math
            daily_qty = 0
            if "three times daily" in dosage: daily_qty = 3
            elif "twice daily" in dosage: daily_qty = 2
            elif "once daily" in dosage or "daily" in dosage: daily_qty = 1

            if daily_qty > 0:
                days_supply = int(qty) / daily_qty
                next_needed = last_purchase + timedelta(days=days_supply)
                days_remaining = (next_needed - today).days

                # Since your data is 2024 and today is 2026, 
                # days_remaining will be a large negative number (e.g. -700)
                print(f"Patient {p_id} | {p_name}: Supply ends {next_needed.date()} | Days Left: {days_remaining}")

                if days_remaining <= 3:
                    print(f"   🚨 ALERT TRIGGERED for {p_name}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")

if __name__ == "__main__":
    diagnostic_test()