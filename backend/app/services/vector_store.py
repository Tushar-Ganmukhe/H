import chromadb
from langfuse import observe
from sentence_transformers import SentenceTransformer

client = chromadb.Client()
collection = client.get_or_create_collection("products")

model = SentenceTransformer("all-MiniLM-L6-v2")

@observe(name="index_products")
def index_products(products):
    for p in products:
        embedding = model.encode(p["product_name"]).tolist()

        collection.add(
            ids=[str(p["product_id"])],
            embeddings=[embedding],
            documents=[p["product_name"]]
        )

# backend/app/services/vector_store.py

@observe(name="search_product")
def search_product(name: str):
    try:
        emb = model.encode(name).tolist()
        results = collection.query(
            query_embeddings=[emb],
            n_results=1
        )

        # Check if results and documents actually exist
        if results and results.get("documents") and len(results["documents"][0]) > 0:
            return results["documents"][0][0]
    except Exception as e:
        print(f"Vector search error: {e}")
    
    return None