import pandas as pd
import numpy as np
import re
from sqlalchemy.orm import Session
from datetime import datetime
from langfuse import observe
from app.core.models import Product
from app.services.vector_store import index_products

class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def _normalize(self, text):
        """Standardizes text: removes symbols, lowercase, and extra spaces"""
        if not text: return ""
        text = re.sub(r'[®™©]', '', str(text))
        return text.strip().lower()

    def _clean_bool(self, val):
        """Helper to convert various Excel formats (Yes/No, 1/0, True/False) to Boolean"""
        if pd.isna(val): return False
        s = str(val).strip().lower()
        return s in ['yes', 'true', '1', '1.0', 'y', 'required']

    @observe(name="get_product_by_name")
    def get_product_by_name(self, name: str):
        """
        AI AGENT SYNC: Fetches real-time data from SQLite.
        Used by chatbot to provide updated prices and stock.
        """
        if not name: return None
        search_term = self._normalize(name)
        
        # Search DB using fuzzy name matching
        product = self.db.query(Product).filter(
            Product.name.ilike(f"%{search_term}%")
        ).first()

        if not product: return None
            
        return {
            "product_id": product.product_id,
            "product_name": product.name,
            "price": product.price,
            "stock": product.stock,
            "prescription_required": product.prescription_required,
            "pzn": product.pzn,
            "package_size": product.package_size
        }

    @observe(name="get_all_products")
    def get_all_products(self):
        """Fetches all inventory for the Admin Dashboard table"""
        return self.db.query(Product).order_by(Product.last_updated.desc()).all()

    @observe(name="update_manual_inventory")
    def update_product(self, product_id: str, updates: dict):
        """Updates a single product from the Admin Dashboard table actions"""
        product = self.db.query(Product).filter(Product.product_id == product_id).first()
        if product:
            if "stock" in updates: product.stock = int(updates["stock"])
            if "price" in updates: product.price = float(updates["price"])
            if "prescription_required" in updates: 
                product.prescription_required = bool(updates["prescription_required"])
            
            product.last_updated = datetime.utcnow()
            self.db.commit()
            self.db.refresh(product)
            return product
        return None

    @observe(name="bulk_upload_inventory_logic")
    def bulk_upload(self, file_path: str):
        """
        EXCEL PROCESSING ENGINE:
        1. Cleans column names and ignores blank rows.
        2. Maps your specific columns to the Database.
        3. Upsert logic: Update if ID exists, else Insert.
        4. Syncs AI Vector Store so chatbot learns new names.
        """
        # Load Excel
        df = pd.read_excel(file_path)
        
        # Clean columns: Trim whitespace and lowercase
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        # Drop rows where 'product id' is missing (Handles blank rows)
        df = df.dropna(subset=['product id'])

        summary = {"added": 0, "updated": 0, "failed": 0, "skipped_blank": 0}
        vector_updates = []

        for _, row in df.iterrows():
            try:
                # 1. Extract and Clean Data
                raw_id = str(row.get('product id')).strip()
                if not raw_id or raw_id.lower() == 'nan':
                    summary["skipped_blank"] += 1
                    continue

                p_id = raw_id
                p_name = str(row.get('product name', 'Unknown')).strip()
                p_price = float(row.get('price rec', 0))
                p_stock = int(row.get('stock', 0))
                p_rx = self._clean_bool(row.get('prescription_required', False))
                
                # Additional fields from your Excel structure
                p_pzn = str(row.get('pzn', '')).strip()
                p_size = str(row.get('package size', '')).strip()
                p_desc = str(row.get('descriptions', '')).strip()
                p_search = str(row.get('search_name', '')).strip()

                # 2. Check if product exists (UPSERT LOGIC)
                existing = self.db.query(Product).filter(Product.product_id == p_id).first()
                
                if existing:
                    # UPDATE existing record
                    existing.name = p_name
                    existing.price = p_price
                    existing.stock = p_stock
                    existing.prescription_required = p_rx
                    existing.pzn = p_pzn
                    existing.package_size = p_size
                    existing.description = p_desc
                    existing.search_name = p_search
                    existing.last_updated = datetime.utcnow()
                    summary["updated"] += 1
                else:
                    # INSERT new record
                    new_product = Product(
                        product_id=p_id,
                        name=p_name,
                        price=p_price,
                        stock=p_stock,
                        prescription_required=p_rx,
                        pzn=p_pzn,
                        package_size=p_size,
                        description=p_desc,
                        search_name=p_search
                    )
                    self.db.add(new_product)
                    summary["added"] += 1
                
                # Collect for AI Vector Store sync
                vector_updates.append({
                    "product_id": p_id,
                    "product_name": p_name
                })
                
            except Exception as e:
                print(f"Row Processing Error: {e}")
                summary["failed"] += 1

        self.db.commit()

        # 3. CRITICAL: Sync AI Vector Store so chatbot recognizes names instantly
        if vector_updates:
            index_products(vector_updates)
            
        return summary