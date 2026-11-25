# Verilabel AI

Snap a label, spot the errors, and choose a better product.

A web app (VTU BE ISE mini project, 2026-27) that reads an Indian packaged-food
label photo using computer vision and OCR, checks it against the FSSAI Labelling
and Display Regulations 2020, gives PASS/FAIL for each mandatory item and a
compliance score, and suggests better alternatives.

Roles: Customer (one photo), Inspector (many photos, marks Reviewed),
Admin (edits FSSAI rules, sees scan history and usage statistics).

## Team and folders

| Member | Role | Folders they edit |
|---|---|---|
| 1 | Platform, Integration and Compliance | Django project files (config/, manage.py), accounts/, scans/, pipeline/, compliance/, contracts/, mocks/, docs/ |
| 2 | AI Vision | ai_vision/, ml_data/, requirements-ai.txt |
| 3 | Frontend, Reports and Role APIs | frontend/, reports/, dashboards/ |

Only edit your own folders. If you need a change somewhere else, ask the owner.

## How a scan flows

1. A user uploads a photo on a Member 3 page.
2. Member 1's upload API saves it and a background task starts.
3. Member 2's ai_vision returns a VISION RESULT (quality, detections, OCR lines).
4. Member 1's compliance code makes EXTRACTED FIELDS, then runs the FSSAI rules
   to make the COMPLIANCE RESULT (PASS/FAIL per rule, score, verdict).
5. Everything is saved in the database.
6. Member 3's pages, PDF report and alternatives show it.

The exact shapes are in contracts/. Sample data is in mocks/.

## Branches

- main: the working project. Only Member 1 merges into main.
- member1-platform, member2-ai, member3-frontend: one branch per member.

See docs/TEAM_GUIDE.md for the exact git steps.

## Setup (Django project is added by Member 1 in the next push)

1. Install Python 3.10+, Git, VS Code.
2. Clone the repo and switch to your branch (see docs/TEAM_GUIDE.md).
3. Create a virtual environment and install packages (commands in docs/TEAM_GUIDE.md).
4. Copy .env.example to .env.
