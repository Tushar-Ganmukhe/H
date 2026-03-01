from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import products, patients, orders, chat, refill, auth, symptoms
from app.services.product_service import ProductService
from app.services.vector_store import index_products

# ✅ LIFESPAN EVENT: Runs when server starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Server starting... Loading products...")
    try:
        # 1. Load products from Excel
        service = ProductService()
        all_products = service.get_all_products()
        
        # 2. Index them into Vector Store (ChromaDB)
        if all_products:
            index_products(all_products)
        else:
            print("⚠️ No products found in Excel to index.")
            
    except Exception as e:
        print(f"❌ Error during startup indexing: {e}")
        
    yield
    print("🛑 Server shutting down...")

app = FastAPI(title="Agentic Pharmacy Backend", lifespan=lifespan)

# ✅ CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include Routers
app.include_router(auth.router)
app.include_router(refill.router)
app.include_router(products.router)
app.include_router(patients.router)
app.include_router(orders.router)
app.include_router(chat.router)
app.include_router(symptoms.router)

@app.get("/")
def root():
    return {"message": "Agentic Pharmacy Backend Running"}