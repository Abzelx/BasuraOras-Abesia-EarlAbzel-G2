# BasuraOras – Account Feature: Step-by-Step Guide

Follow the steps in order. After each step there is a suggested **commit** so your GitHub history shows progress over time.

## Step 0 – Prerequisites
Install Python 3.11+, Git, and PostgreSQL (or make a free Supabase project).
Create a **public** GitHub repo named `BasuraOras-Abesia-Earl-G2` (format SystemName-Lastname-Firstname-Section; change G2 if your section differs).

## Step 1 – Project + virtual environment
```bash
git clone https://github.com/<you>/BasuraOras-Abesia-Earl-G2.git
cd BasuraOras-Abesia-Earl-G2
python -m venv venv
venv\Scripts\activate
pip install "Django>=5.2,<5.3" "psycopg[binary]" dj-database-url python-dotenv
pip freeze > requirements.txt     # (or use the requirements.txt provided)
django-admin startproject config .
```
**Concept:** a virtual environment keeps this project's packages separate. `startproject config .` creates `manage.py` and the `config/` settings folder.
First create `.gitignore` containing `.env`, `venv/`, `__pycache__/` **before your first commit** – secrets pushed once stay in history forever.
> `git add . && git commit -m "Initial Django project, requirements and .gitignore"`

## Step 2 – Secrets in .env
Create `.env` (never committed) and `.env.example` (committed, fake values). `settings.py` reads them with `python-dotenv`, and `dj-database-url` turns `DATABASE_URL` into Django's `DATABASES`. There is deliberately **no SQLite fallback**.
> `git commit -m "Load secrets and PostgreSQL URL from .env"`

## Step 3 – Create the database
Local: `createdb basuraoras` (or pgAdmin). Supabase: Project Settings → Database → copy the URI (use `?sslmode=require`).
Put it in `.env` as `DATABASE_URL`.

## Step 4 – `locations` app (barangay + street)
`python manage.py startapp locations`. Models `Barangay` and `Street` let residents choose where they live.
**Concept:** a model = a database table; a `ForeignKey` = a link between tables.
> `git commit -m "Add Barangay and Street models"`

## Step 5 – Custom user with roles (`accounts/models.py`)
`python manage.py startapp accounts`, then set `AUTH_USER_MODEL = "accounts.User"` **before the first migrate**.
`User` extends `AbstractUser` (so password hashing, sessions, etc. stay built in) and adds `role`, `phone_number`, `street`, `barangay`.
Database constraints enforce: resident ⇒ street; staff ⇒ barangay; email unique ignoring case.
```bash
python manage.py makemigrations locations accounts
python manage.py migrate
python manage.py seed_locations
python manage.py createsuperuser
```
> `git commit -m "Add custom User model with roles and migrations"`

## Step 6 – Registration (`forms.py`, `views.register`)
`RegistrationForm` extends Django's `UserCreationForm`, which already: checks both passwords match, runs password validators, and **hashes** the password (`set_password`). We add email uniqueness, street choice, and force `role=RESIDENT` (so nobody can register themselves as staff).
Success/error text uses the **messages framework** (`messages.success(...)`), shown in `base.html`.
> `git commit -m "Add resident registration with validation and messages"`

## Step 7 – Login / Logout
`LoginView` handles authentication; our `EmailOrUsernameBackend` lets people use either. Wrong credentials → error message. Logout is a **POST** form (Django 5 requirement, protects against CSRF logout).
`LOGIN_URL` makes `@login_required` send logged-out visitors to the login page.
> `git commit -m "Add login/logout and email-or-username backend"`

## Step 8 – Role-based dashboards
`dashboard_redirect` sends each user to their dashboard. Each dashboard view is wrapped in `@role_required(...)` (`accounts/decorators.py`): logged out → login page; wrong role → **403**. So a resident typing `/dashboard/staff/` gets "Access denied".
> `git commit -m "Add role-based dashboards and role_required decorator"`

## Step 9 – Profile
Views use `request.user`, with **no id in the URL**, so a user can never view/edit anyone else. `ProfileForm` lists only editable fields (not role/username), so tampering with the POST does nothing.
> `git commit -m "Add profile view and edit"`

## Step 10 – Tests
```bash
python manage.py test
```
Covers registration rules, hashing, login errors, logout, 403s, and profile isolation. Commit: `git commit -m "Add account feature tests"`.

## Step 11 – Push
```bash
git push origin main
```
Check on GitHub that **`.env` is not there**. Push after every step, not once at the end.

## Try it manually
1. `/register/` as a resident → lands on resident dashboard.
2. In `/admin/` add a user with role **Staff** + a barangay → log in → staff dashboard.
3. Logged in as resident, open `/dashboard/staff/` → 403.
4. Log out, open `/profile/` → redirected to login.

## Quiz yourself
- Why must `AUTH_USER_MODEL` be set before the first migration?
- Where is the password hashed, and what does the DB column contain?
- Why is logout a POST?
- Why no `<id>` in the profile URL?
