from fastapi import FastAPI

app = FastAPI()

@app.post("/fulfill")
def fulfill_order(payload: dict):
    print("📦 Warehouse received order:", payload)
    return {"status": "processing"}