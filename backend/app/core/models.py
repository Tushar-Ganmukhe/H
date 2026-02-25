from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from datetime import datetime
from .database import Base

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    mobile = Column(String, unique=True, index=True) # Future WhatsApp Hook
    created_at = Column(DateTime, default=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    pzn = Column(String, nullable=True)
    price = Column(Float)
    package_size = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    stock = Column(Integer, default=0)
    prescription_required = Column(Boolean, default=False)
    search_name = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    patient_id = Column(String) # Stores Mobile Number or Excel PAT_ID
    product_id = Column(String, ForeignKey("products.product_id"))
    product_name = Column(String)
    quantity = Column(Integer)
    total_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    details = Column(String)
    admin_mobile = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)