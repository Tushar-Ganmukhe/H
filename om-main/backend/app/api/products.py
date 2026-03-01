from fastapi import APIRouter, HTTPException
from langfuse import observe
from app.services.product_service import ProductService
import os
import httpx

router = APIRouter()
service = ProductService()


def translate_text(text: str, target: str = "en") -> str:
    """Simple wrapper around Google Translate REST API."""
    key = os.getenv("GOOGLE_API_KEY")
    if not key or not text:
        return text
    url = "https://translation.googleapis.com/language/translate/v2"
    try:
        resp = httpx.post(url, params={"key": key}, json={"q": text, "target": target, "format": "text"})
        data = resp.json()
        return data.get("data", {}).get("translations", [])[0].get("translatedText", text)
    except Exception:
        return text


@router.get("/products")
@observe(name="get_all_products")
def get_products():
    # reload data so that recent orders/stock changes from other service instances are reflected
    service.reload()
    return service.get_all_products()

@router.get("/products/{product_name}")
@observe(name="get_product_by_name")
def get_product(product_name: str):
    product = service.get_product_by_name(product_name)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/admin/products")
@observe(name="get_admin_products")
def get_admin_products():
    """Return complete product list for admins with translation and analysis."""
    # ensure we have the latest values from disk
    service.reload()
    df = service.df
    products = []
    for _, row in df.iterrows():
        item = {col: row.get(col) for col in df.columns}
        desc = str(row.get("descriptions", ""))
        item["description_en"] = translate_text(desc)
        products.append(item)

    analysis = {
        "total_products": len(df),
        "average_price": float(df.get("price rec").mean()) if "price rec" in df.columns else 0,
        "min_price": float(df.get("price rec").min()) if "price rec" in df.columns else 0,
        "max_price": float(df.get("price rec").max()) if "price rec" in df.columns else 0,
        "by_package_size": df.get("package size").value_counts().to_dict() if "package size" in df.columns else {},
    }
    return {"products": products, "analysis": analysis}