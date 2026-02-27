import chromadb
from langfuse import observe
from sentence_transformers import SentenceTransformer

# -----------------------------
# Initialize Vector DB + Model
# -----------------------------
client = chromadb.Client()
collection = client.get_or_create_collection("products")
model = SentenceTransformer("all-MiniLM-L6-v2")


# -----------------------------
# Index Products
# -----------------------------
@observe(name="index_products")
def index_products(products):
    """
    Indexes product name + description for semantic search.
    Safe for re-runs (avoids duplicate ID crash).
    """
    for p in products:
        try:
            desc = p.get("description", "")
            search_content = f"{p['product_name']} {desc}"

            embedding = model.encode(search_content).tolist()

            collection.upsert(   # 🔥 use upsert instead of add (safer)
                ids=[str(p["product_id"])],
                embeddings=[embedding],
                documents=[search_content],
                metadatas=[{
                    "name": p["product_name"],
                    "description": desc
                }]
            )

        except Exception as e:
            print(f"Indexing error for {p.get('product_name')}: {e}")


# -----------------------------
# Product Name Search (with threshold protection)
# -----------------------------
@observe(name="search_product")
def search_product(name: str):
    """
    Searches product by name.
    Includes relaxed threshold (1.6) to handle typos & cross-language matches.
    Prevents hallucinated corrections.
    """
    try:
        if collection.count() == 0:
            return None

        emb = model.encode(name).tolist()

        results = collection.query(
            query_embeddings=[emb],
            n_results=1,
            include=["metadatas", "distances"]
        )

        if results and results.get("metadatas") and len(results["metadatas"][0]) > 0:
            distance = results["distances"][0][0]

            if distance < 1.6:
                print(f"✅ Strong Match (Distance: {distance})")
                return results["metadatas"][0][0]["name"]
            else:
                print(f"⚠️ Weak Match (Distance: {distance}) → Rejected")
                return None

    except Exception as e:
        print(f"Vector search error: {e}")

    return None


# -----------------------------
# Single Best Match by Symptom
# -----------------------------
@observe(name="search_by_symptom")
def search_by_symptom(symptom_query: str):
    """
    Returns the single most relevant product based on symptom meaning.
    """
    try:
        if collection.count() == 0:
            return None

        emb = model.encode(symptom_query).tolist()

        results = collection.query(
            query_embeddings=[emb],
            n_results=1,
            include=["metadatas"]
        )

        if results and results.get("metadatas") and len(results["metadatas"][0]) > 0:
            return results["metadatas"][0][0]["name"]

    except Exception as e:
        print(f"Symptom search error: {e}")

    return None


# -----------------------------
# Shortlist Candidates (Stage 2 for LLM filtering)
# -----------------------------
@observe(name="search_symptoms_shortlist")
def search_symptoms_shortlist(query: str, n: int = 5):
    """
    Returns top N candidates for LLM / Pharmacist agent reasoning.
    """
    try:
        if collection.count() == 0:
            return []

        emb = model.encode(query).tolist()

        results = collection.query(
            query_embeddings=[emb],
            n_results=n,
            include=["metadatas"]
        )

        if results and results.get("metadatas"):
            return [m["name"] for m in results["metadatas"][0]]

    except Exception as e:
        print(f"Shortlist search error: {e}")

    return []