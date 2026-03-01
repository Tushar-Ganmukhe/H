import json
import os
import httpx
import re
from langfuse import observe
from sentence_transformers import SentenceTransformer
import numpy as np

from app.services.vector_store import search_product

# Translation cache file
TRANSLATION_CACHE_FILE = "translation_cache.json"

# Symptom keywords are only a small hint; matching is primarily semantic.
SYMPTOM_KEYWORDS = {
    "headache": ["kopfschmerz", "kopfschmerzen", "migraine", "headache"],
    "fever": ["fieber", "fever", "temperature"],
    "cough": ["husten", "cough"],
    "stomach": ["magen", "stomach", "bauch", "darm"],
    # keep other categories but they are optional hints
}

# Keywords that indicate a product is actually suitable for a given symptom
# (used as a hard filter / annotation after semantic scoring).
SUITABILITY_KEYWORDS = {
    # keywords that indicate the product treats the given symptom
    "fever": [
        "fieber", "fever", "antipyretic", "fever reducer",
        "ibuprofen", "paracetamol", "acetaminophen", "fiebersenkend",
        "naproxen",
        # note: omit generic terms like "pain" or "schmerz" which can appear
        # in unrelated product descriptions (e.g. probiotics mentioning
        # "Bauchschmerzen") and lead to false positives.
    ],
    "headache": [
        "kopfschmerz", "headache", "migraine", "analgesic", "pain",
        " ibuprofen", " acetaminophen", "acetaminophen"
    ],
    # you can add more categories as needed
}


class SymptomMatcher:
    def __init__(self):
        # Lightweight sentence transformer for semantic matching
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.translation_cache = self._load_translation_cache()
        self.google_api_key = os.getenv("GOOGLE_API_KEY")

    def _load_translation_cache(self):
        if os.path.exists(TRANSLATION_CACHE_FILE):
            try:
                with open(TRANSLATION_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_translation_cache(self):
        try:
            with open(TRANSLATION_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _detect_language(self, text: str) -> str:
        if not text:
            return "en"
        german_chars = sum(1 for c in text.lower() if c in "äöüß")
        common_german = {"der", "die", "das", "und", "mit", "zu", "für", "in", "von"}
        words = set(text.lower().split())
        german_words = len(words & common_german)
        if german_chars > max(1, len(text) * 0.02) or german_words >= 2:
            return "de"
        return "en"

    @observe(name="translate_text")
    def translate_text(self, text: str, target_lang: str = "en") -> str:
        if not text:
            return ""
        text = text.strip()
        cache_key = f"{text}|{target_lang}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        detected = self._detect_language(text)
        if detected == target_lang:
            self.translation_cache[cache_key] = text
            self._save_translation_cache()
            return text

        if not self.google_api_key:
            # No API key: return original text but cache result to avoid repeated checks
            self.translation_cache[cache_key] = text
            self._save_translation_cache()
            return text

        try:
            url = "https://translation.googleapis.com/language/translate/v2"
            resp = httpx.post(
                url,
                params={"key": self.google_api_key},
                json={"q": text, "target": target_lang, "format": "text"},
                timeout=5.0,
            )
            resp.raise_for_status()
            data = resp.json()
            translated = data.get("data", {}).get("translations", [])[0].get("translatedText", text)
            self.translation_cache[cache_key] = translated
            self._save_translation_cache()
            return translated
        except Exception:
            # On failure, return original
            self.translation_cache[cache_key] = text
            self._save_translation_cache()
            return text

    def _extract_symptom_keywords(self, symptom: str) -> list:
        if not symptom:
            return []
        s = symptom.lower()
        matched = []
        for cat, kws in SYMPTOM_KEYWORDS.items():
            for kw in kws:
                if kw in s:
                    matched.append(cat)
                    break
        return matched

    @observe(name="semantic_similarity")
    def calculate_similarity(self, text1: str, text2: str) -> float:
        try:
            v1 = self.model.encode(text1)
            v2 = self.model.encode(text2)
            # cosine
            num = float(np.dot(v1, v2))
            den = float(np.linalg.norm(v1) * np.linalg.norm(v2))
            if den == 0:
                return 0.0
            return max(0.0, min(1.0, num / den))
        except Exception:
            return 0.0

    @observe(name="match_symptom_to_products")
    def match_symptom_to_products(self, symptom: str, products: list, threshold: float = 0.35) -> dict:
        """Return ranked product matches for a symptom.

        Behavior:
        - Compute semantic similarity between symptom and each product (name+description).
        - Use keyword hints to slightly boost scores (small, non-hardcoded boost).
        - If no good results, fallback to vector-store search to retrieve candidates.
        - Always return top candidates (dynamic), even if below threshold.
        """
        if not symptom:
            return {"symptom": symptom, "matches": [], "symptom_categories": [], "total_matches": 0}

        symptom_categories = self._extract_symptom_keywords(symptom)

        matched = []

        # Build quick lookup for stock/price by product name
        name_to_product = { (p.get("product_name") or "").strip(): p for p in (products or []) }

        # Score all provided products
        def _is_suitable_for_categories(name: str, desc: str, categories: list) -> bool:
            """Return True if product contains any of the suitability keywords for all categories."""
            text = (name + " " + desc).lower()
            for cat in categories:
                kws = SUITABILITY_KEYWORDS.get(cat, [])
                if kws:
                    # require at least one keyword for this category
                    if not any(kw in text for kw in kws):
                        return False
            return True

        for p in (products or []):
            name = p.get("product_name") or ""
            desc = str(p.get("description") or "")
            if not name and not desc:
                continue
            trans_desc = self.translate_text(desc, "en")
            combined = f"{name}. {trans_desc}"
            sim = self.calculate_similarity(symptom, combined)

            # small keyword boost
            boost = 0.0
            s_low = symptom.lower()
            text_low = (trans_desc + " " + name).lower()
            for cat in symptom_categories:
                for kw in SYMPTOM_KEYWORDS.get(cat, []):
                    if kw in text_low or kw in s_low:
                        boost += 0.05

            score = min(1.0, sim + boost)
            suitable = _is_suitable_for_categories(name, trans_desc, symptom_categories)
            matched.append({
                "product_name": name,
                "price": p.get("price", 0),
                "stock": p.get("stock", 0),
                "similarity": round(score, 3),
                "description": trans_desc,
                "original_description": desc,
                "suitable": suitable,
            })

        # If we found nothing or top scores are weak, fallback to vector-store
        if not matched or max([m["similarity"] for m in matched], default=0) < threshold:
            try:
                candidates = search_product(symptom, n_results=10) or []
                for c in candidates:
                    cname = c.get("name")
                    cdesc = c.get("description", "")
                    combined = f"{cname}. {cdesc}"
                    sim = self.calculate_similarity(symptom, combined)
                    prod = name_to_product.get(cname) or {}
                    matched.append({
                        "product_name": cname,
                        "price": prod.get("price", c.get("price", 0)),
                        "stock": prod.get("stock", 0),
                        "similarity": round(sim, 3),
                        "description": self.translate_text(cdesc, "en"),
                        "original_description": cdesc,
                    })
            except Exception:
                pass

        # Deduplicate by product_name keeping highest score
        by_name = {}
        for m in matched:
            key = (m.get("product_name") or "").strip()
            if not key:
                continue
            if key not in by_name or m.get("similarity", 0) > by_name[key].get("similarity", 0):
                by_name[key] = m

        results = list(by_name.values())
        results.sort(key=lambda x: x.get("similarity", 0), reverse=True)

        # Filter out results that aren't suitable (based on keywords) when we have symptom categories
        if symptom_categories:
            suitable_results = [r for r in results if r.get("suitable", True)]
        else:
            suitable_results = results

        # Return those above threshold; if none, return top 3 as dynamic fallback
        final = [r for r in suitable_results if r.get("similarity", 0) >= threshold]
        if not final and suitable_results:
            # fallback to top N even if similarity < threshold
            final = suitable_results[:3]
        elif not final and results:
            # if no suitable results, fall back to original results but mark unsuitable
            final = results[:3]

        # ensure each returned record has a suitable flag (default True)
        for r in final:
            r.setdefault("suitable", True)

        return {
            "symptom": symptom,
            "matches": final,
            "symptom_categories": symptom_categories,
            "total_matches": len(final),
        }

    @observe(name="generate_symptom_response")
    def generate_response(self, symptom: str, matches: list) -> str:
        if not matches:
            return (
                f"🔍 I searched our inventory for '{symptom}', but didn't find specific matches. "
                f"Please consult a doctor or pharmacist for medical advice. You can also describe your symptoms in more detail."
            )

        resp = f"💊 **Recommended Medicines for '{symptom}'**\n\n"
        for i, m in enumerate(matches, 1):
            name = m.get("product_name")
            price = m.get("price", 0)
            stock = m.get("stock", 0)
            sim = m.get("similarity", 0) * 100
            desc = m.get("description", "")
            stock_indicator = "✅" if stock > 0 else "❌"
            suitable = m.get("suitable", True)
            resp += f"{i}. **{name}**\n"
            resp += f"   Price: ${price} per unit\n"
            resp += f"   Stock: {stock_indicator} {stock} units available\n"
            resp += f"   Match: {sim:.0f}% relevant\n"
            resp += f"   Info: {desc[:120]}\n"
            if not suitable:
                resp += "   ⚠️ Not suitable for this symptom\n"
            resp += "\n"
        resp += "Would you like to order any of these medicines?"
        return resp
