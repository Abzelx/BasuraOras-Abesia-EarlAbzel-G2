# PD2 Guide – Missed Collection Reporting (core feature)

## Part 1 – What you are building (the vertical slice)
```
Database      locations.Street  ──<  pickups.CollectionSchedule  ──<  pickups.MissedReport  >──  accounts.User
Backend       forms_*.py (validation)  ·  views_*.py (logic)  ·  urls_*.py (routes)
Frontend      pickups/templates/pickups/*.html  (+ dashboards, nav)
```
- **Model** = table. `CollectionSchedule` says *when* a street is collected; `MissedReport` says *a resident says it didn't happen*.
- **Form** = validation. All the business rules (7-day window, weekday must match, max 3/day …) are in `forms_reports.py`.
- **View** = who may do what. Look at `report_detail`: `get_object_or_404(MissedReport, pk=pk, user=request.user)`. Because it filters by the logged-in user, another resident's report simply does not exist for you → 404.
- **Role decorator** `@role_required(...)` (from PD1) keeps residents out of staff pages (403).
- **DB constraints** (UniqueConstraint / CheckConstraint) are the last line of defence even if code has a bug.

CRUD map: **C**reate report (resident) · **R**ead own reports (resident) / barangay reports (staff) · **U**pdate description (resident, while Submitted) and status+response (staff) · **D**elete: schedules can be deleted when unused (otherwise deactivated, BR-11). Reports are **never deleted** by design (BR-25) – mention this in your report.

## Part 2 – Run it
1. Copy the new/changed files into your project (the zip is the whole project; overwrite).
2. `python manage.py makemigrations locations accounts pickups` → creates `pickups/migrations/0001_initial.py`.
3. `python manage.py migrate` (applies to Supabase).
4. In `/admin/` add a **Staff** user (role Staff + barangay) → `python manage.py seed_schedules`.
5. `python manage.py test` → everything should say OK.
6. Try it: resident → "Report a missed collection" → staff → Reports → Acknowledge → Resolve.

## Part 3 – Git branching (required: main / develop / feature branches / PRs)
Rules: never commit directly to `main`; one branch per feature; merge with Pull Requests; **don't delete merged branches**.

**Setup (once).** Make sure everything from PD1 is already pushed to `main`, then:
```bash
git checkout main
git pull
git checkout -b develop
git push -u origin develop
```
Also protect `main` on GitHub: Settings → Branches → Add rule for `main` → "Require a pull request before merging".

### Branch 1 – `feature/collection-schedule`
```bash
git checkout develop
git checkout -b feature/collection-schedule
```
Add these files / edits, committing as you go:
| Commit | Files |
|---|---|
| `Add pickups app and CollectionSchedule model` | `pickups/__init__.py`, `apps.py`, `models/schedule.py`, `models/__init__.py` (only `from .schedule import CollectionSchedule`), settings: add `"pickups"` to `INSTALLED_APPS`, then run `makemigrations pickups` and add `pickups/migrations/` |
| `Add schedule form with time and street validation` | `forms_schedule.py` |
| `Add staff schedule CRUD views and templates` | `views_schedule.py`, `urls_schedule.py`, `urls.py` (only the schedule import: `urlpatterns = schedule_urls`), `config/urls.py` include, `templates/pickups/schedule_*.html`, CSS |
| `Register schedule in admin and add seed command` | `admin.py` (schedule only), `management/commands/seed_schedules.py` |
| `Add schedule tests` | `tests/__init__.py`, `tests/base.py`, `tests/test_schedule.py` |

> Tip: for the shared files above, keep only the lines for the feature you're on; the next branch adds the rest. If this feels fiddly you can add whole files per branch – just make sure the site still starts (`python manage.py check`) before every commit.

Push and open a PR **into `develop`**:
```bash
git push -u origin feature/collection-schedule
```
On GitHub: "Compare & pull request" → base **develop** ← compare **feature/collection-schedule** → write what you did → Create → **Merge pull request** (do not delete the branch).

### Branch 2 – `feature/missed-report-submission`
```bash
git checkout develop && git pull
git checkout -b feature/missed-report-submission
```
| Commit | Files |
|---|---|
| `Add MissedReport model with status and DB constraints` | `models/report.py`, `models/__init__.py` (add the report import), `makemigrations pickups` |
| `Add report form with 7-day, weekday and daily-limit rules` | `forms_reports.py`, `utils.py` |
| `Add resident views to create, list, view and edit reports` | `views_reports.py`, `urls_reports.py`, `urls.py` (add report urls), `templates/pickups/report_*.html` |
| `Add report submission tests` | `tests/test_reports.py` |

Push → PR into `develop` → merge.

### Branch 3 – `feature/staff-report-review`
```bash
git checkout develop && git pull
git checkout -b feature/staff-report-review
```
| Commit | Files |
|---|---|
| `Add staff review form with allowed status transitions` | `forms_review.py` |
| `Add staff report list and review views` | `views_review.py`, `urls_review.py`, `urls.py` (add review urls), `templates/pickups/staff_report_*.html` |
| `Register MissedReport in admin` | `admin.py` (report part) |
| `Add staff review tests` | `tests/test_review.py` |

Push → PR into `develop` → merge.

### Branch 4 – `feature/dashboard-integration`
```bash
git checkout develop && git pull
git checkout -b feature/dashboard-integration
```
| Commit | Files |
|---|---|
| `Show next collection and recent reports on resident dashboard` | `accounts/views.py`, `accounts/templates/accounts/resident_dashboard.html` |
| `Show report and schedule counts on staff dashboard` | `accounts/templates/accounts/staff_dashboard.html` |
| `Add role-based navigation links` | `templates/base.html` |
| `Update README with core feature and setup steps` | `README.md`, `docs/PD2_GUIDE.md` |

Push → PR into `develop` → merge. That's **4 feature branches and 4 merged PRs into develop** (minimum is 2 and 2).

### Release – `develop` → `main`
```bash
git checkout develop && git pull
python manage.py test        # must pass
```
On GitHub open a PR with base **main** ← compare **develop** → merge. Do not delete any branch.

### Final step – completion report
Fill in the PD Completion Report template, save as PDF `BasuraOras-Abesia-Earl-G2-PD2.pdf`, add it to `docs/` through a small branch + PR (`docs/add-pd2-report`), e.g. commit message `Add PD2 completion report`.

## Part 4 – Check yourself
1. Why does `report_detail` use `user=request.user` in the query instead of an `if` check?
2. Which rule makes a 4th report in one day fail, and where is it coded?
3. What happens if staff try to delete a schedule that already has reports? Why?
4. Why can't a resident change the status by adding `status=RESOLVED` to the edit POST?
5. Why is `now_local()` in `utils.py` instead of calling `timezone.now()` directly in the form?
