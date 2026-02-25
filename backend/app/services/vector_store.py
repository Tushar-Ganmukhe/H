import chromadb
from langfuse import observe
from sentence_transformers import SentenceTransformer

client = chromadb.Client()
collection = client.get_or_create_collection("products")

model = SentenceTransformer("all-MiniLM-L6-v2")

@observe(name="index_products")
def index_products(products):
    """Indexes product name and description for semantic symptom search."""
    for p in products:
        # We combine name and description to create a rich searchable document
        desc = p.get("description", "")
        search_content = f"{p['product_name']} {desc}"
        embedding = model.encode(search_content).tolist()

        collection.add(
            ids=[str(p["product_id"])],
            embeddings=[embedding],
            documents=[search_content],
            metadatas=[{"name": p["product_name"]}]
        )

@observe(name="search_product")
def search_product(name: str):
    try:
        emb = model.encode(name).tolist()
        results = collection.query(query_embeddings=[emb], n_results=1)
        if results and results.get("documents") and len(results["documents"][0]) > 0:
            # Return the metadata name if available
            return results["metadatas"][0][0]["name"]
    except Exception as e:
        print(f"Vector search error: {e}")
    return None

@observe(name="search_by_symptom")
def search_by_symptom(symptom_query: str):
    """Semantic search to find medicines based on user symptoms."""
    try:
        emb = model.encode(symptom_query).tolist()
        results = collection.query(query_embeddings=[emb], n_results=1)
        if results and results.get("metadatas") and len(results["metadatas"][0]) > 0:
            return results["metadatas"][0][0]["name"]
    except Exception as e:
        print(f"Symptom search error: {e}")
    return None