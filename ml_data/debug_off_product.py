"""Show which image fields Open Food Facts returns for ONE product.
Run:  python ml_data/debug_off_product.py BARCODE
"""
import json
import sys
import urllib.request

if len(sys.argv) < 2:
    print("Usage: python ml_data/debug_off_product.py BARCODE")
    sys.exit(1)

code = sys.argv[1]
fields = "code,images,selected_images,image_front_url,image_ingredients_url,image_nutrition_url"
url = "https://world.openfoodfacts.org/api/v2/product/%s.json?fields=%s" % (code, fields)
request = urllib.request.Request(
    url, headers={"User-Agent": "VerilabelAI-VTU-MiniProject/1.0 (student project)"}
)

try:
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
except Exception as error:
    print("Request failed:", error)
    print("If this says 503, wait a few minutes and run it again.")
    sys.exit(1)

product = data.get("product") or {}
print("status:", data.get("status_verbose", data.get("status")))
print("image_front_url:      ", product.get("image_front_url"))
print("image_ingredients_url:", product.get("image_ingredients_url"))
print("image_nutrition_url:  ", product.get("image_nutrition_url"))
print("selected_images kinds:", list((product.get("selected_images") or {}).keys()))
print("all image keys:       ", list((product.get("images") or {}).keys()))