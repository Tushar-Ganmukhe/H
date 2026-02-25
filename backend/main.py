from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.database import engine, Base
from app.api import products, patients, orders, chat, refill, admin, auth

# Critical: Creates 'patients' and 'orders' tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agentic Pharmacy System - Pro")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect Routers (Ensure auth is included)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(refill.router)
app.include_router(products.router)
app.include_router(patients.router)
app.include_router(orders.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"status": "online", "mode": "Level-3 Hybrid Persistence"}