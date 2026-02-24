from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import shutil
import os

from app.core.database import get_db
from app.core.models import Product, Order, AuditLog
from app.services.product_service import ProductService
from langfuse import observe

router = APIRouter(prefix="/admin", tags=["Admin Operations"])

# -------------------------------------------------------------------------
# 1. INVENTORY RETRIEVAL (Ensures data shows on Refresh)
# -------------------------------------------------------------------------

@router.get("/inventory")
def get_all_inventory(db: Session = Depends(get_db)):
    """
    Fetches all inventory from SQLite. 
    This is what the frontend calls every time you reload the page.
    """
    # Query all products, ordered by last update (newest first)
    products = db.query(Product).order_by(Product.last_updated.desc()).all()
    return products

# -------------------------------------------------------------------------
# 2. MANUAL MODIFICATION (Syncs manual edits to DB)
# -------------------------------------------------------------------------

@router.put("/inventory/{product_id}")
@observe(name="admin_manual_update")
def update_product_manual(product_id: str, updates: dict, db: Session = Depends(get_db)):
    """Handles manual edits from the Dashboard Edit Icon"""
    service = ProductService(db)
    updated_product = service.update_product(product_id, updates)
    
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Log action for Langfuse and Security
    db.add(AuditLog(
        action="MANUAL_UPDATE",
        details=f"Admin updated {product_id}: {str(updates)}",
        admin_mobile="9999999999"
    ))
    db.commit()
    
    return {"message": "Success", "product": updated_product}

# -------------------------------------------------------------------------
# 3. BULK EXCEL UPLOAD (Permanent Storage)
# -------------------------------------------------------------------------

@router.post("/upload-inventory")
@observe(name="admin_bulk_upload")
async def bulk_upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Processes Excel, maps columns, skips blanks, and SAVES to SQLite"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files allowed")

    # Save temporary file for pandas processing
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        service = ProductService(db)
        # Process Excel and COMMIT to Database
        summary = service.bulk_upload(temp_path)
        
        # Log to Audit Table
        db.add(AuditLog(
            action="BULK_UPLOAD",
            details=f"Excel Sync: {summary['added']} added, {summary['updated']} updated",
            admin_mobile="9999999999"
        ))
        db.commit()
        
        return summary
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Server Error during Sync: {str(e)}")
    finally:
        # Cleanup: Remove the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

# -------------------------------------------------------------------------
# 4. SALES ANALYTICS (Real-time DB Reports)
# -------------------------------------------------------------------------

@router.get("/analytics/sales-report")
def get_sales_report(db: Session = Depends(get_db)):
    """Calculates Trends and Best Sellers based on saved Orders"""
    daily_sales = db.query(
        func.date(Order.created_at).label("date"),
        func.sum(Order.total_price).label("revenue")
    ).group_by(func.date(Order.created_at)).all()

    top_products = db.query(
        Order.product_name,
        func.sum(Order.quantity).label("total_sold")
    ).group_by(Order.product_name).order_by(func.sum(Order.quantity).desc()).limit(5).all()

    return {
        "daily_trends": [{"date": str(r.date), "revenue": r.revenue} for r in daily_sales],
        "best_sellers": [{"name": r.product_name, "quantity": r.total_sold} for r in top_products]
    }