
# Pipeline Contract (owned by Member 1, agreed by all three members)

Do not change this alone. Tell the group first. Member 1 updates this file.

Coordinates: every "box" is [x1, y1, x2, y2] in pixels of the ORIGINAL uploaded image.
Dates are written as YYYY-MM-DD. Confidence is a number from 0 to 1.

## 1. Scan statuses

queued, processing, done, failed, low_quality

## 2. VISION RESULT (Member 2 produces, Member 1 reads)

Sample: mocks/vision_result_sample.json

- image_quality: status ("ok" or "too_low") and reason (text, empty if ok)
- detections: list of items, each with
  - class: one of the 7 names listed in section 9 below
  - confidence
  - box
- ocr_lines: list of items, each with
  - text
  - confidence
  - box
  - language: "en" or "hi"

Member 2 provides ONE function: ai_vision.analyze_image(image_path) which returns this.

## 3. EXTRACTED FIELDS (Member 1 produces from the VISION RESULT)

Sample: mocks/extracted_fields_sample.json

Every field below is an object with: found (true/false), value, confidence.

- food_name
- ingredients
- nutrition (value is a set of numbers: energy_kcal, protein_g, carbohydrate_g,
  total_sugars_g, total_fat_g, saturated_fat_g, sodium_mg)
- allergens
- net_quantity
- manufacturing_date
- expiry_date
- fssai_licence_number
- manufacturer_address
- veg_nonveg_mark (value is "veg" or "nonveg")

## 4. COMPLIANCE RESULT (Member 1 produces from EXTRACTED FIELDS + detections + rules)

Sample: mocks/compliance_result_sample.json

- image_quality_warning: text, or null if the image was fine
- rules: list of items, each with rule_id, name, status ("PASS" or "FAIL"), reason
- score: number 0 to 100
- verdict: "COMPLIANT", "PARTIAL" or "NON_COMPLIANT" (Member 1 may tune the limits)

The 11 rules are R01 to R11, one per mandatory item (food name, ingredients,
nutrition information, allergen declaration, veg/non-veg symbol, net quantity,
manufacturing date, expiry or best-before date, FSSAI logo, FSSAI licence number,
manufacturer address). They are stored as editable data, not hard-coded.

## 5. SCAN RECORD (what the scan API returns to the pages)

Sample: mocks/scan_record_sample.json

scan_id, batch_id (null for a single customer upload), status, image_url,
uploaded_by (user_id, name, role), created_at, extracted_fields,
compliance_result, review (status "pending" or "reviewed", reviewed_by, reviewed_at).

## 6. Mock switch

In .env, USE_MOCK_VISION=True makes Member 1's pipeline use mocks/vision_result_sample.json
instead of calling ai_vision. Set it to False when Member 2's step is merged.

## 7. Low-quality scans (added in Stage 3)

If the VISION RESULT says image_quality is "too_low", the scan status becomes "low_quality".
compliance_result then holds image_quality_warning (the reason), an empty rules list,
and score and verdict set to null. extracted_fields stays null.
If anything crashes, the status becomes "failed" and the scan has an error message.

## 8. Additions (after Member 3's questions)

The SCAN RECORD now also has two top-level fields:
- product_name: text, empty "" if no product name was found
- score: number 0 to 100, or null for scans that are queued, processing, failed or low_quality

Verdict values are exactly COMPLIANT, PARTIAL and NON_COMPLIANT, or null when the scan has no result.
Member 1 sets the score limits for each verdict in Stage 4. Pages must show the verdict as given and must not work it out from the score.

## 9. Detection classes (changed after Member 2's labelling work)

The allowed values of detections[].class are now exactly these 7 names (lowercase, underscores):

veg_symbol, nonveg_symbol, nutrition_table, allergen, fssai_no, ingredients, fssai_logo

The VISION RESULT shape is unchanged. Only the allowed class values grew.
image_quality and ocr_lines are unchanged.

Rules for Member 2:

- Boxes are in pixels of the ORIGINAL uploaded image, the same as the ocr_lines boxes.
  If your detector resizes the image (for example to 640 pixels), convert the boxes back before returning them.
- A class that is not detected is simply missing from the list. Do not invent detections.
- Labelling guide:
  - ingredients = the whole ingredients paragraph
  - nutrition_table = the whole table with its heading
  - allergen = the allergen statement (for example the "Contains ..." text)
  - fssai_no = the "Lic. No." text including the digits
  - fssai_logo = only the logo graphic
  - veg_symbol / nonveg_symbol = the whole square symbol

How Member 1 uses them:

- ingredients box -> ingredients text
- nutrition_table box -> nutrition values
- fssai_no box -> licence number
- allergen box -> allergen statement
- veg_symbol / nonveg_symbol -> rule R05
- fssai_logo -> rule R09

A missing detection is not treated as proof that the item is absent. The text step also checks the OCR lines.
