from app.services.product_service import ProductService
from app.services.symptom_matcher import SymptomMatcher

ps = ProductService()
m = SymptomMatcher()
products = ps.get_all_products()
res = m.match_symptom_to_products('i fell fever', products, threshold=0.5)
print(res['symptom_categories'], 'total', res['total_matches'])
for item in res['matches']:
    print(item['product_name'], 'sim', item['similarity'], 'suitable', item.get('suitable'))
