from app.services.product_service import ProductService
ps=ProductService()
for p in ps.get_all_products():
    if "Kijimea" in p.get("product_name", ""):
        print(p.get("product_name"))
        print("description:", p.get("description"))
        break
