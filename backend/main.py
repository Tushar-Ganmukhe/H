from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import products, patients, orders, chat

app = FastAPI(title="Agentic Pharmacy Backend")

# ✅ CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include Routers
from app.api import refill
app.include_router(refill.router)
app.include_router(products.router)
app.include_router(patients.router)
app.include_router(orders.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {"message": "Agentic Pharmacy Backend Running"}
