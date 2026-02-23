from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import shutil
import os

from app.core.database import get_db
from app.core.models import Product, Order, AuditLog
from app.services.product_service import ProductService
from langfuse import observe

router = APIRouter(prefix="/admin", tags=["Admin Operations"])

# ---------------------------------------------------------
# 1. INVENTORY MANAGEMENT ROUTES
# ---------------------------------------------------------

@router.get("/inventory")
def get_all_inventory(db: Session = Depends(get_db)):
    """Fetches all products for the Admin Table (Real-time sync)"""
    service = ProductService(db)
    return service.get_all_products()

@router.put("/inventory/{product_id}")
@observe(name="admin_manual_update")
def update_product_manual(product_id: str, updates: dict, db: Session = Depends(get_db)):
    """Handles manual edits from the 'Save' icon in the dashboard table"""
    service = ProductService(db)
    updated_product = service.update_product(product_id, updates)
    
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Audit Log for Security
    db.add(AuditLog(
        action="MANUAL_UPDATE",
        details=f"Admin updated {product_id}: {str(updates)}",
        admin_mobile="9999999999" # In production, get this from auth context
    ))
    db.commit()
    
    return {"message": "Success", "product": updated_product}

@router.post("/upload-inventory")
@observe(name="admin_bulk_upload_api")
async def bulk_upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Handles Excel Bulk Uploads. 
    Synchronizes Database and AI Vector Store.
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an Excel file.")

    # Save temp file for processing
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        service = ProductService(db)
        # Execute logic (Upsert + Cleaning + Vector Sync)
        summary = service.bulk_upload(temp_path)
        
        # Log the bulk action for auditing
        db.add(AuditLog(
            action="BULK_UPLOAD",
            details=f"Excel Sync Result -> Added: {summary['added']}, Updated: {summary['updated']}, Skipped: {summary['skipped_blank']}",
            admin_mobile="9999999999"
        ))
        db.commit()
        
        return summary
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        # Always remove temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ---------------------------------------------------------
# 2. SALES ANALYTICS ROUTES
# ---------------------------------------------------------

@router.get("/analytics/sales-report")
def get_sales_report(db: Session = Depends(get_db)):
    """
    Calculates Data for the Recharts visualization:
    1. Daily Revenue Trend (Line Chart)
    2. Best Selling Products (Bar Chart)
    """
    # 7-day window for trends
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # SQL aggregation for Daily Selling Report
    daily_sales = db.query(
        func.date(Order.created_at).label("date"),
        func.sum(Order.total_price).label("revenue"),
        func.count(Order.id).label("order_count")
    ).filter(Order.created_at >= seven_days_ago)\
     .group_by(func.date(Order.created_at)).all()

    # SQL aggregation for Best-selling products
    top_products = db.query(
        Order.product_name,
        func.sum(Order.quantity).label("total_sold")
    ).group_by(Order.product_name)\
     .order_by(func.sum(Order.quantity).desc())\
     .limit(5).all()

    return {
        "daily_trends": [
            {"date": str(row.date), "revenue": row.revenue, "orders": row.order_count} 
            for row in daily_sales
        ],
        "best_sellers": [
            {"name": row.product_name, "quantity": row.total_sold} 
            for row in top_products
        ]
    }