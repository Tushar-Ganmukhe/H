from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. Import Database engine and Base to create tables
from app.core.database import engine, Base
from app.api import products, patients, orders, chat, refill, admin

# ---------------------------------------------------------
# DATABASE INITIALIZATION
# This line creates the 'pharmacy.db' file and all tables
# automatically based on the models we defined.
# ---------------------------------------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agentic Pharmacy System - Pro")

# ✅ CORS Setup: Essential for React to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include All Routers
# We keep your existing chat/patient routers and add the new Admin router
app.include_router(chat.router)
app.include_router(refill.router)
app.include_router(products.router)
app.include_router(patients.router)
app.include_router(orders.router)

# NEW: The brain of your Admin Portal
app.include_router(admin.router)

@app.get("/")
def root():
    return {
        "message": "Agentic Pharmacy Backend Running",
        "database": "SQLite Connected",
        "status": "Ready"
    }