import chromadb
from langfuse import observe
from sentence_transformers import SentenceTransformer

# Initialize ChromaDB (In-memory for simplicity, or save to disk)
client = chromadb.Client()

# Load the AI Model
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_collection():
    """Helper to get or create collection"""
    return client.get_or_create_collection("products")

@observe(name="index_products")
def index_products(products):
    """
    1. Deletes old index.
    2. Creates new embeddings with Description.
    """
    print("🔄 Re-indexing products with descriptions...")
    try:
        client.delete_collection("products")
    except:
        pass
    
    collection = client.create_collection("products")
    
    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for p in products:
        p_id = str(p["product_id"])
        name = str(p["product_name"])
        desc = str(p.get("description", ""))
        price = float(p.get("price", 0))

        # ✅ CRITICAL: Embed "Name + Description" so we can search by symptom
        # We combine them so searching "Cough" finds "Mucosolvan"
        text_to_embed = f"{name}. {desc}"
        
        embedding = model.encode(text_to_embed).tolist()

        ids.append(p_id)
        embeddings.append(embedding)
        documents.append(name) 
        metadatas.append({"price": price, "description": desc, "name": name})

    if ids:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
    print(f"✅ Successfully indexed {len(ids)} products.")

@observe(name="search_product")
def search_product(query: str, n_results=1):
    collection = get_collection()
    try:
        emb = model.encode(query).tolist()
        results = collection.query(
            query_embeddings=[emb],
            n_results=n_results
        )

        # Check if we have results
        if results and results.get("documents") and len(results["documents"][0]) > 0:
            
            matches = []
            for i in range(len(results["documents"][0])):
                meta = results["metadatas"][0][i]
                matches.append({
                    "name": meta["name"],
                    "description": meta["description"],
                    "price": meta["price"]
                })
            
            # If asking for 1 result (for ordering), return just the name string
            if n_results == 1:
                return matches[0]["name"]
            
            # If asking for recommendations (symptom check), return full details
            return matches

    except Exception as e:
        print(f"❌ Vector search error: {e}")
    
    return [] if n_results > 1 else None