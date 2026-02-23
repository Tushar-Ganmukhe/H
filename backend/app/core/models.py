from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from datetime import datetime
from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True) # Maps to 'product id'
    name = Column(String, index=True) # Maps to 'product name'
    pzn = Column(String, nullable=True) # Maps to 'pzn'
    price = Column(Float) # Maps to 'price rec'
    package_size = Column(String, nullable=True) # Maps to 'package size'
    description = Column(Text, nullable=True) # Maps to 'descriptions'
    stock = Column(Integer, default=0) # Maps to 'stock'
    prescription_required = Column(Boolean, default=False) # Maps to 'prescription_required'
    search_name = Column(String, nullable=True) # Maps to 'search_name'
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    patient_id = Column(String)
    product_id = Column(String, ForeignKey("products.product_id"))
    product_name = Column(String)
    quantity = Column(Integer)
    total_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String) # e.g., "MANUAL_UPDATE", "BULK_UPLOAD"
    details = Column(String)
    admin_mobile = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)