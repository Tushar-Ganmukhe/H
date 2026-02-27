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

    # -------------------------------------------------
    # TEXT NORMALIZATION (for AI + fuzzy matching)
    # -------------------------------------------------
    def _normalize(self, text):
        if not text:
            return ""
        text = re.sub(r'[®™©]', '', str(text))
        return text.strip().lower()

    # -------------------------------------------------
    # SMART PRODUCT LOOKUP
    # -------------------------------------------------
    @observe(name="get_product_by_name")
    def get_product_by_name(self, name: str):
        """
        Hybrid Retrieval Logic:
        1. Exact match
        2. Case-insensitive match
        3. Partial match fallback
        """

        if not name:
            return None

        normalized_name = self._normalize(name)

        # 1️⃣ Exact match
        product = self.db.query(Product).filter(
            Product.name == name
        ).first()

        # 2️⃣ Case insensitive match
        if not product:
            product = self.db.query(Product).filter(
                Product.name.ilike(name)
            ).first()

        # 3️⃣ Partial match fallback
        if not product:
            product = self.db.query(Product).filter(
                Product.name.ilike(f"%{normalized_name}%")
            ).first()

        if not product:
            return None

        return {
            "product_id": product.product_id,
            "product_name": product.name,
            "price": product.price,
            "stock": product.stock,
            "description": product.description or "No description available.",
            "prescription_required": product.prescription_required,
            "dosage_frequency": product.search_name or "As directed"
        }

    # -------------------------------------------------
    # INVENTORY RETRIEVAL
    # -------------------------------------------------
    @observe(name="get_all_products")
    def get_all_products(self):
        return self.db.query(Product).all()

    @observe(name="get_all_product_names")
    def get_all_product_names(self):
        return [p.name for p in self.db.query(Product.name).all()]

    # -------------------------------------------------
    # LLM SYMPTOM REASONING DATA
    # -------------------------------------------------
    @observe(name="get_all_products_for_llm_recommendation")
    def get_all_products_for_llm_recommendation(self):
        return [
            {
                "product_name": p.name,
                "description": p.description,
                "stock": p.stock,
                "price": p.price
            }
            for p in self.db.query(Product).all()
        ]

    # -------------------------------------------------
    # MANUAL INVENTORY UPDATE + VECTOR SYNC
    # -------------------------------------------------
    @observe(name="update_manual_inventory")
    def update_product(self, product_id: str, updates: dict):

        product = self.db.query(Product).filter(
            Product.product_id == product_id
        ).first()

        if not product:
            return None

        if "stock" in updates:
            product.stock = int(updates["stock"])

        if "price" in updates:
            product.price = float(updates["price"])

        if "prescription_required" in updates:
            product.prescription_required = bool(updates["prescription_required"])

        if "description" in updates:
            product.description = updates["description"]

        if "dosage_frequency" in updates:
            product.search_name = updates["dosage_frequency"]

        product.last_updated = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(product)

            # 🔄 Real-time Vector Sync
            index_products([{
                "product_id": product.product_id,
                "product_name": product.name,
                "description": product.description
            }])

        except Exception:
            self.db.rollback()
            raise

        return product

    # -------------------------------------------------
    # BULK UPLOAD LOGIC
    # -------------------------------------------------
    @observe(name="bulk_upload_inventory_logic")
    def bulk_upload(self, file_path: str):

        df = pd.read_excel(file_path, header=None, skiprows=1)

        summary = {"added": 0, "updated": 0, "failed": 0}
        vector_updates = []

        for index, row in df.iterrows():
            try:
                p_id = str(row[0]).strip()
                p_name = str(row[1]).strip()

                if p_id.lower() in ["nan", "none", ""]:
                    continue

                p_price = float(row[3]) if pd.notnull(row[3]) else 0.0
                p_desc = str(row[5]) if pd.notnull(row[5]) else ""
                p_stock = int(float(row[6])) if pd.notnull(row[6]) else 0
                p_dosage = str(row[7]) if pd.notnull(row[7]) else "As directed"

                existing = self.db.query(Product).filter(
                    Product.product_id == p_id
                ).first()

                if existing:
                    existing.stock += p_stock
                    existing.price = p_price
                    existing.description = p_desc
                    existing.search_name = p_dosage
                    summary["updated"] += 1
                else:
                    new_product = Product(
                        product_id=p_id,
                        name=p_name,
                        price=p_price,
                        stock=p_stock,
                        description=p_desc,
                        search_name=p_dosage,
                        prescription_required=False
                    )
                    self.db.add(new_product)
                    summary["added"] += 1

                vector_updates.append({
                    "product_id": p_id,
                    "product_name": p_name,
                    "description": p_desc
                })

            except Exception as e:
                print(f"❌ Row {index} failed: {e}")
                summary["failed"] += 1

        try:
            self.db.commit()
            if vector_updates:
                index_products(vector_updates)
        except Exception:
            self.db.rollback()
            raise

        return summary