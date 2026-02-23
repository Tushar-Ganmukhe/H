import pandas as pd
import numpy as np
import re
from langfuse import observe

PRODUCT_FILE = r"C:\Users\hp\OneDrive\New folder\OneDrive\Desktop\products-export.xlsx"

class ProductService:
    def __init__(self):
        try:
            # Load Excel
            self.df = pd.read_excel(PRODUCT_FILE, header=0) 
            # Clean column names (removes spaces and makes lowercase)
            self.df.columns = [str(col).strip().lower() for col in self.df.columns]
            
            # Ensure 'product name' exists and is string
            if 'product name' in self.df.columns:
                self.df['product name'] = self.df['product name'].astype(str)
        except Exception as e:
            print(f"❌ Excel Loading Error: {e}")
            self.df = pd.DataFrame()

    def _normalize(self, text):
        """Standardizes text: removes symbols (®, ™), lowercase, and extra spaces"""
        if not text: return ""
        # Remove special characters
        text = re.sub(r'[®™©]', '', str(text))
        # Lowercase and strip
        return text.strip().lower()

    @observe(name="get_product_by_name")
    def get_product_by_name(self, name: str):
        if not name or self.df.empty:
            return None
            
        search_term = self._normalize(name)

        # 1. Create a cleaned version of the 'product name' column for searching
        # This helps match "Cystinol akut" with "Cystinol akut®"
        self.df['temp_clean_name'] = self.df['product name'].apply(self._normalize)
        
        # 2. Search using 'contains' so "Paracetamol" matches the full long name in your Excel
        mask = self.df['temp_clean_name'].str.contains(search_term, regex=False)
        matches = self.df[mask]

        if matches.empty:
            return None
            
        # Get the first match
        row = matches.iloc[0].to_dict()

        # 3. MAP YOUR SPECIFIC COLUMNS
        # Your screenshot shows column 'price rec', we map it to 'price' for the agent
        return {
            "product_id": row.get("product id", "N/A"),
            "product_name": row.get("product name"),
            "price": row.get("price rec", 0) # ✅ Maps 'price rec' from your screenshot
        }

    @observe(name="get_all_products")
    def get_all_products(self):
        """Return all products from Excel file"""
        if self.df.empty:
            return []
        
        products = []
        for _, row in self.df.iterrows():
            products.append({
                "product_id": row.get("product id", "N/A"),
                "product_name": row.get("product name"),
                "price": row.get("price rec", 0)
            })
        return products