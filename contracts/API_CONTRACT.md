# API Contract (owned by Member 1, agreed by all three members)

All paths start with /api/. Logged-in calls send the header:
Authorization: Token <token>
Data is sent and returned as JSON, except photo upload (multipart form) and the PDF download.

## Login and sign up (Member 1)
| Method | Path | Body | Returns |
|---|---|---|---|
| POST | /api/auth/signup/ | name, user_id, password, role | user (name, user_id, role) |
| POST | /api/auth/signin/ | user_id, password | token, user, or an error message |
| GET | /api/auth/me/ | none | the logged-in user |

role is "customer", "inspector" or "admin".

## Scans (Member 1)
| Method | Path | Notes |
|---|---|---|
| POST | /api/scans/ | Customer: form field "image" (one photo). Inspector: form field "images" (many). Returns scan_id and status (inspector: batch_id and a list). Rejects wrong file type or size with a clear message. |
| GET | /api/scans/ | The logged-in user's scans, newest first (list of SCAN RECORDS). |
| GET | /api/scans/<scan_id>/ | One SCAN RECORD. Pages repeat this call until status is done, failed or low_quality. |

## Report and alternatives (Member 3)
| Method | Path | Notes |
|---|---|---|
| GET | /api/scans/<scan_id>/report/ | Downloads the PDF compliance report. |
| GET | /api/scans/<scan_id>/alternatives/ | List of better products (name, category, why it is better). |

## Inspector (Member 3)
| Method | Path | Notes |
|---|---|---|
| GET | /api/inspector/batches/ | The inspector's batches with counts of compliant and non-compliant. |
| GET | /api/inspector/batches/<batch_id>/ | All SCAN RECORDS in a batch. |
| POST | /api/inspector/scans/<scan_id>/review/ | Marks a scan as Reviewed (needs a confirmation text from the inspector). |

## Admin (Member 3, using Member 1's rule functions)
| Method | Path | Notes |
|---|---|---|
| GET | /api/admin/rules/ | List all FSSAI rules. |
| POST | /api/admin/rules/ | Add a rule. |
| PUT | /api/admin/rules/<rule_id>/ | Update a rule. |
| GET | /api/admin/history/ | Scan history and top scanned products. |
| GET | /api/admin/stats/ | Numbers for the usage graphs. |

## Pages (Member 3, files go in frontend/templates/)
1. signin.html   2. upload.html   3. progress.html   4. result.html
5. inspector.html   6. admin_rules.html   7. admin_stats.html

## Additions (after Member 3's questions)

### Customer history page
history.html is a new page owned by Member 3 (so there are now 8 pages).
It calls GET /api/scans/. Each item has scan_id, product_name, created_at (the date), status, score
(plus the other SCAN RECORD fields). The list is the logged-in user's own scans, newest first.

### Upload (confirmed)
Customer: form field "image". Response 201: {"scan_id": 1, "status": "queued"}.
Inspector: form field "images" (many). Response 201: {"batch_id": 1, "scans": [{"scan_id": 1, "status": "queued"}]}.
Problems return 400 with {"error": "message"}.

### Alternatives (Member 3 builds it, these names are fixed)
GET /api/scans/<scan_id>/alternatives/ returns a list of objects with exactly: name, category, why.
An empty list [] means there is no suggestion (for example, nutrition values were not found).

### Report (Member 3 builds it)
GET /api/scans/<scan_id>/report/ sends a PDF with Content-Type: application/pdf.
It needs the Authorization: Token header like every other call.
Only the scan's owner or an Admin can download it. Anyone else gets 404 {"error": "Scan not found."}.
If the scan is not "done", it returns 400 {"error": "The report is not ready yet."}.
A plain link cannot send the token header, so the page must use fetch with the header, turn the response into a file (blob) and start the download.

### Verdict colours (for pages)
COMPLIANT = green, PARTIAL = amber, NON_COMPLIANT = red, null = grey "Not available".
## Inspector reviews customer scans too (decided after Member 3's question, guide to confirm)

Inspectors can review any customer scan, and scans from their own batches.
Without this, a customer would never see a review status.

- GET /api/scans/<scan_id>/ now also works for an Inspector when the scan belongs to a customer.
  (Everything else is still 404 "Scan not found." for other people's scans.)
  Member 3: for the report download use the same rule: from scans.permissions import can_view_scan.
- NEW (Member 3 builds): GET /api/inspector/customer-scans/ returns SCAN RECORDS of all customers' scans
  with status "done", newest first. Optional filter: ?review=pending or ?review=reviewed.
  Only Inspectors and Admins may call it, anyone else gets 403.
- POST /api/inspector/scans/<scan_id>/review/ (Member 3 builds) works for customer scans and for the
  inspector's own batch scans. Body: {"confirmation": "text typed by the inspector"}.
  It sets review status "reviewed", reviewed_by, reviewed_at and review_note, and returns the updated SCAN RECORD.
  Errors (400): scan not done yet, already reviewed, or empty confirmation text.
- The customer sees the result in review: status ("pending" or "reviewed"), reviewed_by (the inspector's ID)
  and reviewed_at. History shows "Not reviewed yet" only when status is "pending".
- Page: Member 3 may add a new page inspector_customers.html (or a tab on inspector.html) for this list.
## Admin rules (Stage 4 decisions)
A rule object has exactly these fields: rule_id, name, check_type, field_key, weight (1 to 10), enabled (true or false).

check_type values: field_found, detection_found, nutrition_values, allergen_declared, fssai_licence_14
field_key:
- for field_found: one of food_name, ingredients, nutrition, allergens, net_quantity, manufacturing_date,
  expiry_date, fssai_licence_number, manufacturer_address, veg_nonveg_mark
- for detection_found: one of the 7 YOLO classes (see section 9 of PIPELINE_CONTRACT.md)
- for nutrition_values: comma-separated nutrient names from energy_kcal, protein_g, carbohydrate_g,
  total_sugars_g, total_fat_g, saturated_fat_g, sodium_mg
- for allergen_declared and fssai_licence_14: ignored

Member 3's Admin API calls these functions (from compliance.services import list_rules, create_rule, update_rule):
- list_rules() returns a list of rule objects, including switched-off rules
- create_rule(data) returns the new rule (rule_id is made automatically, like R12, if not given)
- update_rule(rule_id, data) returns the updated rule; data may hold only the fields to change
They raise ValueError with a message the page can show. The API returns that as 400 {"error": "message"}.
Rules in the database are used for every new scan. Changing a rule does not change old scans.
## Decisions after Member 3's questions (Stage 4)

### Sign-up and roles
- POST /api/auth/signup/ body: name, user_id, password. role is optional and defaults to "customer".
- Only customers can sign up on their own. Inspector accounts are created by an Admin (endpoints below).
  Admin accounts are created by Member 1 with "python manage.py createsuperuser".
- Sign-up keeps the three fields name, ID and password (the user_id is not made from the name, because names
  can repeat and may have spaces). user_id may only have letters, digits and @ . + - _ (no spaces).

### Review block in a SCAN RECORD
review has status ("pending" or "reviewed"), reviewed_by, reviewed_at and review_note.
POST /api/inspector/scans/<id>/review/ (Member 3) saves the Scan fields review_status = "reviewed",
reviewed_by = the inspector, reviewed_at = now, review_note = the confirmation text.

### Admin creates inspector logins (Member 3 builds the endpoints)
- GET /api/admin/inspectors/ returns a list of {user_id, name, role, date_joined}. Use accounts.services.list_inspectors().
- POST /api/admin/inspectors/ body {user_id, name, password}. Returns 201 with the new inspector (no password).
  Use accounts.services.create_inspector(data). It raises ValueError with a message, return it as 400 {"error": "message"}.

### Rules API (Member 3 builds)
- GET /api/admin/rules/ uses list_rules(). POST /api/admin/rules/ uses create_rule(data), returns 201.
- PUT /api/admin/rules/<rule_id>/ uses update_rule(rule_id, data). It accepts partial data.
- ValueError means 400 {"error": "message"}. compliance.services.RuleNotFound (a ValueError subclass) means 404.
- Rule fields are exactly: rule_id, name, check_type, field_key, weight (1 to 10), enabled.
  Weights are relative importance and do not need to add up to 100. A switched-off rule is skipped and does not
  appear in compliance_result.rules. The score is recalculated over the remaining rules.
  rule_id in compliance_result.rules is the same as Rule.rule_id.

### Permissions and errors
- Use accounts.permissions.IsAdminRole and accounts.permissions.IsInspectorOrAdmin as permission_classes.
- Authentication is DRF TokenAuthentication (header Authorization: Token <token>), set for all views by default.
- Every error is {"error": "message"}, including 401 and 403. Only sign-up field problems use {"errors": {...}}.

### Wiring (done by Member 1)
- config/urls.py includes reports.urls and dashboards.urls under the prefix api/.
  Member 3 replaces both urls.py files. Routes are written without the api/ prefix, for example
  path('admin/rules/', ...) in dashboards/urls.py and path('scans/<int:scan_id>/report/', ...) in reports/urls.py.
  Inspector routes also go in dashboards/urls.py, for example path('inspector/customer-scans/', ...).
- INSTALLED_APPS already has dashboards and reports.

### Pages
Any file frontend/templates/<name>.html is served at /app/<name>/ as a plain file (no template tags such as {% %}).
CSS and JS go in frontend/static/ and are linked as /static/css/x.css and /static/js/x.js.
/ redirects to /app/signin/. Pass ids in the address, for example /app/result/?scan_id=5.
Pages keep the token in the browser (localStorage) and call the API with relative paths like /api/scans/.