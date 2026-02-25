import pandas as pd
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
        """Standardizes text for AI matching"""
        if not text: return ""
        text = re.sub(r'[®™©]', '', str(text))
        return text.strip().lower()

    @observe(name="get_product_by_name")
    def get_product_by_name(self, name: str):
        """AI AGENT SYNC: Returns full medical profile from SQLite."""
        if not name: return None
        search_term = self._normalize(name)
        
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
            "description": product.description,
            "dosage_frequency": product.search_name # Mapped from Column H
        }

    @observe(name="update_manual_inventory")
    def update_product(self, product_id: str, updates: dict):
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
        """Processes Excel using column indices (A=0, B=1, D=3, F=5, G=6, H=7)."""
        df = pd.read_excel(file_path, header=None, skiprows=1)
        summary = {"added": 0, "updated": 0, "failed": 0}
        vector_updates = []

        for index, row in df.iterrows():
            try:
                p_id = str(row[0]).strip()
                p_name = str(row[1]).strip()
                if p_id.lower() in ['nan', 'none', '']: continue

                p_price = float(row[3]) if pd.notnull(row[3]) else 0.0
                p_desc = str(row[5]) if pd.notnull(row[5]) else "" 
                p_stock = int(float(row[6])) if pd.notnull(row[6]) else 0
                p_dosage = str(row[7]) if pd.notnull(row[7]) else "As directed"

                existing = self.db.query(Product).filter(Product.product_id == p_id).first()
                if existing:
                    existing.stock = int(existing.stock) + p_stock
                    existing.description = p_desc
                    existing.price = p_price
                    existing.search_name = p_dosage
                    summary["updated"] += 1
                else:
                    new_p = Product(product_id=p_id, name=p_name, price=p_price, stock=p_stock, description=p_desc, search_name=p_dosage)
                    self.db.add(new_p)
                    summary["added"] += 1
                self.db.commit()
                vector_updates.append({"product_id": p_id, "product_name": p_name, "description": p_desc})
            except Exception as e:
                self.db.rollback()
                print(f"❌ Row {index} fail: {e}")
                summary["failed"] += 1
        
        if vector_updates: index_products(vector_updates)
        return summary