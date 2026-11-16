# BasuraOras

Barangay garbage-collection schedule app (Django + PostgreSQL). This milestone is the **Account feature**:
registration, login/logout, role-based dashboards (Resident / Barangay Staff), and user profile.

## Setup
```bash
python -m venv venv
venv\Scripts\activate            # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env   -> then edit .env
python manage.py migrate
python manage.py seed_locations  # sample barangay + streets
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000/

## Roles
- **Resident** – self-registers, picks a street/purok, sees the resident dashboard.
- **Barangay Staff** – created by an admin in `/admin/` (set role = Staff + barangay), sees the staff dashboard.

## Tests
```bash
python manage.py test
```
(The database user needs permission to create a test database.)
