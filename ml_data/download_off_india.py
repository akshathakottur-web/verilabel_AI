"""Download Indian product images from Open Food Facts (Member 2).

Run from the repo root:  python ml_data/download_off_india.py
Asks the site ONLY for products that have a nutrition photo, then
ones that have an ingredients photo.
Uses only Python's built-in libraries.
Retries when the server is busy (HTTP 503 etc.).
Skips files already downloaded; keeps existing credits.csv rows.
"""
import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

# One pass per filter. Each pass collects up to WANT_PER_PASS new products.
FILTERS = ["en:nutrition-photo-selected", "en:ingredients-photo-selected"]
WANT_PER_PASS = 60
PAGE_SIZE = 50
MAX_PAGES = 40
MAX_TRIES = 5
OUT_DIR = os.path.join("ml_data", "raw_photos", "openfoodfacts_india")
CREDITS_PATH = os.path.join(OUT_DIR, "credits.csv")
API = "https://world.openfoodfacts.org/api/v2/search"
HEADERS = {"User-Agent": "VerilabelAI-VTU-MiniProject/1.0 (student project)"}
FIELDS = (
    "code,product_name,brands,"
    "image_front_url,image_ingredients_url,image_nutrition_url,"
    "selected_images"
)
KINDS = ["front", "ingredients", "nutrition"]


def get(url):
    """Download a URL and return the bytes. Retries if the server is busy."""
    wait = 10
    for attempt in range(1, MAX_TRIES + 1):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code == 404 or attempt == MAX_TRIES:
                raise
            print("  Server said HTTP %d. Waiting %d s, then retrying (%d/%d)..."
                  % (error.code, wait, attempt, MAX_TRIES))
        except Exception as error:
            if attempt == MAX_TRIES:
                raise
            print("  Problem: %s. Waiting %d s, then retrying (%d/%d)..."
                  % (error, wait, attempt, MAX_TRIES))
        time.sleep(wait)
        wait *= 2


def find_image_url(product, kind):
    url = product.get("image_%s_url" % kind)
    if url:
        return url
    selected = product.get("selected_images") or {}
    block = selected.get(kind) or {}
    display = block.get("display") or {}
    if isinstance(display, dict):
        for language_url in display.values():
            if language_url:
                return language_url
    return None


def download_best(url):
    """Try the full-size version of a photo, then the given one."""
    if ".400.jpg" in url:
        try:
            return get(url.replace(".400.jpg", ".full.jpg"))
        except Exception:
            pass
    return get(url)


def load_credits():
    rows = {}
    if os.path.exists(CREDITS_PATH):
        with open(CREDITS_PATH, newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)
            for row in reader:
                if row:
                    rows[row[0]] = row
    return rows


def save_credits(rows):
    with open(CREDITS_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["barcode", "product_name", "brands", "source_page"])
        writer.writerows(rows.values())


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    credits = load_credits()
    saved = {"front": 0, "ingredients": 0, "nutrition": 0}

    for state in FILTERS:
        print("=== Filter:", state, "===")
        new_products = 0
        page = 1

        while new_products < WANT_PER_PASS and page <= MAX_PAGES:
            params = {
                "countries_tags_en": "india",
                "states_tags": state,
                "fields": FIELDS,
                "page_size": PAGE_SIZE,
                "page": page,
            }
            url = API + "?" + urllib.parse.urlencode(params)
            print("Asking page", page)

            try:
                data = json.loads(get(url).decode("utf-8"))
            except Exception as error:
                print("Could not get this page even after retrying:", error)
                break

            print("Total products matching this filter:", data.get("count"))
            products = data.get("products", [])
            print("Products on this page:", len(products))
            if not products:
                break

            for product in products:
                if new_products >= WANT_PER_PASS:
                    break
                code = str(product.get("code", "unknown"))
                urls = {kind: find_image_url(product, kind) for kind in KINDS}
                if not urls["ingredients"] and not urls["nutrition"]:
                    continue

                got_any_new = False
                for kind in KINDS:
                    image_url = urls[kind]
                    if not image_url:
                        continue
                    ext = os.path.splitext(urllib.parse.urlparse(image_url).path)[1] or ".jpg"
                    path = os.path.join(OUT_DIR, "%s_%s%s" % (code, kind, ext))
                    if os.path.exists(path):
                        continue
                    try:
                        content = download_best(image_url)
                        with open(path, "wb") as file:
                            file.write(content)
                        saved[kind] += 1
                        got_any_new = True
                        time.sleep(0.5)
                    except Exception as error:
                        print("Could not download", image_url, error)

                if got_any_new:
                    new_products += 1
                    credits[code] = [
                        code,
                        product.get("product_name", ""),
                        product.get("brands", ""),
                        "https://world.openfoodfacts.org/product/" + code,
                    ]

            print("So far in this pass: %d new products, new files: %s" % (new_products, saved))
            save_credits(credits)
            page += 1
            time.sleep(2)

    save_credits(credits)
    print("New files saved this run:", saved)
    print("Folder:", OUT_DIR)


main()