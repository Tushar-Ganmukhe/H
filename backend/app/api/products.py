from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.product_service import ProductService
from langfuse import observe

router = APIRouter()

@router.get("/products")
@observe(name="get_all_products_api")
def get_products(db: Session = Depends(get_db)):
    """Fetches all products from the SQLite database"""
    service = ProductService(db)
    return service.get_all_products()

@router.get("/products/{product_name}")
@observe(name="get_product_by_name_api")
def get_product(product_name: str, db: Session = Depends(get_db)):
    """Searches for a specific product by name in the database"""
    service = ProductService(db)
    product = service.get_product_by_name(product_name)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product