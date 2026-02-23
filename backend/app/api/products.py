from fastapi import APIRouter, HTTPException
from langfuse import observe
from app.services.product_service import ProductService

router = APIRouter()
service = ProductService()

@router.get("/products")
@observe(name="get_all_products")
def get_products():
    return service.get_all_products()

@router.get("/products/{product_name}")
@observe(name="get_product_by_name")
def get_product(product_name: str):
    product = service.get_product_by_name(product_name)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product