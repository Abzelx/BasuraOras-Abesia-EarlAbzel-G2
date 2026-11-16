# BasuraOras

Barangay garbage-collection schedule app (Django templates + PostgreSQL/Supabase).

## Features
**Standard features (Project Development 1)** – registration, login/logout, role-based dashboards (Resident / Barangay Staff), user profile.

**Core feature (Project Development 2): Missed Collection Reporting**
A resident reports that a scheduled pickup on their street did not happen. Barangay staff review the report and move it through its life-cycle.

| Who | What they can do |
|---|---|
| Resident | File a report for a scheduled collection of **their own street** (last 7 days), view their own reports (filter by status), edit the description while it is still *Submitted* |
| Staff | See reports for **their own barangay**, acknowledge / resolve / dismiss with a response (dismissal needs an explanation), manage collection schedules (add, edit, delete or deactivate) for their barangay's streets |

Business rules enforced (SDD): BR-08–BR-11 (schedules), BR-20–BR-25 (reports) – e.g. one report per schedule per date, max 3 reports per 24 h, status flow `SUBMITTED → ACKNOWLEDGED → RESOLVED` or `→ DISMISSED`, final statuses can't change, reports are never deleted.
Data lives in three tables: `locations_street` → `pickups_collectionschedule` → `pickups_missedreport` (linked to `accounts_user` twice: reporter and handler).

## Setup
```bash
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env  -> fill in SECRET_KEY and DATABASE_URL (Supabase)
python manage.py makemigrations locations accounts pickups
python manage.py migrate
python manage.py seed_locations  # sample barangay + streets
python manage.py createsuperuser
python manage.py runserver
```
Then in `/admin/` create a **staff** user (role = Staff, barangay = the sample barangay) and run `python manage.py seed_schedules` for sample collection days. Open http://127.0.0.1:8000/

## Tests
```bash
python manage.py test
```
(The database user needs permission to create a test database.)

## Git workflow
`main` (stable) ← `develop` (integration) ← `feature/*`. See `docs/PD2_GUIDE.md`.
