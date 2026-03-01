import os
import re
import time

import openpyxl
import pandas as pd
from langfuse import observe

PRODUCT_FILE = os.getenv("PRODUCT_FILE", "D:\products-export.xlsx")


class ProductService:
    def __init__(self):
        self.reload()

    def reload(self):
        """Reload product inventory from Excel."""
        try:
            self.df = pd.read_excel(PRODUCT_FILE, header=0)
            self.df.columns = [str(col).strip().lower() for col in self.df.columns]
            if "product name" in self.df.columns:
                self.df["product name"] = self.df["product name"].astype(str)
        except Exception as e:
            print(f"Excel loading error: {e}")
            self.df = pd.DataFrame()

    def _normalize(self, text: str) -> str:
        if not text:
            return ""
        cleaned = re.sub(r"[®™©]", "", str(text))
        return re.sub(r"\s+", " ", cleaned).strip().lower()

    def _coerce_stock(self, value) -> int:
        if pd.isna(value):
            return 0
        try:
            return max(0, int(float(value)))
        except Exception:
            return 0

    def _build_product(self, row: dict) -> dict:
        description = row.get(
            "descriptions",
            row.get(
                "short descriptions",
                row.get(
                    "product descriptions",
                    row.get("description", "No description available for this medicine."),
                ),
            ),
        )
        return {
            "product_id": row.get("product id", "N/A"),
            "product_name": row.get("product name"),
            "price": row.get("price rec", 0),
            "stock": self._coerce_stock(row.get("stock", 0)),
            "description": str(description),
        }

    @observe(name="get_product_by_name")
    def get_product_by_name(self, name: str):
        if not name or self.df.empty or "product name" not in self.df.columns:
            return None

        search_term = self._normalize(name)
        if not search_term:
            return None

        temp = self.df.copy()
        temp["temp_clean_name"] = temp["product name"].apply(self._normalize)

        # Prefer exact normalized match to avoid ambiguous contains picks.
        exact_matches = temp[temp["temp_clean_name"] == search_term]
        if not exact_matches.empty:
            matches = exact_matches
        else:
            contains_mask = temp["temp_clean_name"].str.contains(search_term, regex=False)
            matches = temp[contains_mask]

        if matches.empty:
            return None

        # If multiple candidates match, prefer the one with highest stock.
        ranked = matches.copy()
        ranked["_stock_int"] = ranked["stock"].apply(self._coerce_stock) if "stock" in ranked.columns else 0
        ranked = ranked.sort_values(by="_stock_int", ascending=False)
        row = ranked.iloc[0].to_dict()
        return self._build_product(row)

    def check_stock_availability(self, product_name: str, quantity: int):
        """Check if enough stock is available for order."""
        self.reload()
        product = self.get_product_by_name(product_name)
        if not product:
            return False, "Product not found"

        available = self._coerce_stock(product.get("stock", 0))
        if available < int(quantity):
            return False, f"Only {available} units available (requested {quantity})"

        return True, "Stock available"

    def reduce_stock(self, product_name: str, quantity: int):
        """Reduce product stock after successful order."""
        self.reload()
        if self.df.empty or "product name" not in self.df.columns:
            return False

        search_term = self._normalize(product_name)
        self.df["temp_clean_name"] = self.df["product name"].apply(self._normalize)

        exact = self.df[self.df["temp_clean_name"] == search_term]
        if not exact.empty:
            idx = exact.index[0]
        else:
            mask = self.df["temp_clean_name"].str.contains(search_term, regex=False)
            if mask.sum() == 0:
                return False
            idx = self.df[mask].index[0]

        current_stock = self._coerce_stock(self.df.loc[idx, "stock"])
        new_stock = max(0, current_stock - int(quantity))
        self.df.loc[idx, "stock"] = new_stock

        result = self._save_with_openpyxl(product_name, new_stock)
        self.reload()
        return result

    def _save_with_openpyxl(self, product_name: str, new_stock: int, max_retries=3):
        try:
            wb = openpyxl.load_workbook(PRODUCT_FILE)
            ws = wb.active

            product_col = None
            stock_col = None
            for col_idx in range(1, ws.max_column + 1):
                header = ws.cell(row=1, column=col_idx).value
                if header and "product name" in str(header).lower():
                    product_col = col_idx
                if header and "stock" in str(header).lower():
                    stock_col = col_idx

            if not product_col or not stock_col:
                wb.close()
                print("Could not find product name or stock column")
                return False

            normalized_search = self._normalize(product_name)
            for row_idx in range(2, ws.max_row + 1):
                product_cell = ws.cell(row=row_idx, column=product_col)
                stock_cell = ws.cell(row=row_idx, column=stock_col)

                if not product_cell.value:
                    continue

                cell_normalized = self._normalize(str(product_cell.value))
                if cell_normalized == normalized_search or normalized_search in cell_normalized:
                    stock_cell.value = int(new_stock)
                    for attempt in range(max_retries):
                        try:
                            wb.save(PRODUCT_FILE)
                            wb.close()
                            return True
                        except PermissionError:
                            if attempt < max_retries - 1:
                                time.sleep(1 + attempt)
                            else:
                                wb.close()
                                print("Excel file locked; stock updated in memory only")
                                return False

            wb.close()
            print(f"Product '{product_name}' not found in Excel")
            return False
        except Exception as e:
            print(f"openpyxl save error: {str(e)[:100]}")
            return False

    @observe(name="get_all_products")
    def get_all_products(self):
        if self.df.empty:
            return []

        products = []
        for _, row in self.df.iterrows():
            products.append(self._build_product(row.to_dict()))
        return products
