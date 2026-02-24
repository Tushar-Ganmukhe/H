from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# 1. Import Database engine and Base to ensure tables exist
from app.core.database import engine, Base
# 2. Import all Routers to keep all features connected
from app.api import products, patients, orders, chat, refill, admin

# -------------------------------------------------------------------------
# DATABASE INITIALIZATION
# This creates the 'pharmacy.db' file and all required tables 
# (Inventory, Orders, Logs) if they don't already exist.
# -------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agentic Pharmacy System - Pro")

# ✅ CORS Setup: Essential for the React Frontend to talk to this Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Connect All Endpoints (Routers)
# This ensures Chat, Refill, and Orders keep working while adding Admin features
app.include_router(chat.router)
app.include_router(refill.router)
app.include_router(products.router)
app.include_router(patients.router)
app.include_router(orders.router)
app.include_router(admin.router)

@app.get("/")
def root():
    """Health check endpoint to verify project status"""
    return {
        "status": "online",
        "database": "SQLite Connected",
        "features": ["AI Chat", "Refill Alerts", "Inventory Sync", "Analytics"],
        "db_location": os.path.abspath("pharmacy.db")
    }