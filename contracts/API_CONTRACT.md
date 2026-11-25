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
