# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Quick start (Windows / PowerShell)
Commands are taken from `README.md`.

```pwsh
py -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py runserver
```

## Common commands
### Run the app (dev server)
```pwsh
.\.venv\Scripts\python manage.py runserver
```

### Database migrations
```pwsh
.\.venv\Scripts\python manage.py makemigrations
.\.venv\Scripts\python manage.py migrate
```

### Tests
Run all tests:

```pwsh
.\.venv\Scripts\python manage.py test
```

Run a single app’s tests:

```pwsh
.\.venv\Scripts\python manage.py test polls
```

Run a single test module/class/method (Django supports dotted paths):

```pwsh
# module
.\.venv\Scripts\python manage.py test polls.tests

# class
.\.venv\Scripts\python manage.py test polls.tests.SomeTestCase

# single test
.\.venv\Scripts\python manage.py test polls.tests.SomeTestCase.test_something
```

### Lint / format
No lint/format tooling is configured in-repo (no `pyproject.toml`, `ruff.toml`, `setup.cfg`, `tox.ini`, etc.). If you add tooling, document the commands here.

## High-level architecture
This is a minimal Django project based on the official “polls” tutorial.

### Key modules and how requests flow
- `manage.py` is the entry point for Django management commands; it sets `DJANGO_SETTINGS_MODULE=config.settings`.
- `config/settings.py` defines global project settings:
  - `INSTALLED_APPS` includes `polls.apps.PollsConfig`.
  - Uses SQLite (`db.sqlite3` at repo root).
  - Templates use `APP_DIRS=True`, so app templates under `polls/templates/` are discovered automatically.
- `config/urls.py` is the top-level URL router:
  - `/admin/` routes to Django admin.
  - `/` includes `polls.urls`.
- `polls/urls.py` defines app routes (currently only `""` -> `polls.views.index`).
- `polls/views.py` contains the `index` view:
  - Queries `Question` ordered by `-pub_date` (latest 5).
  - Renders `polls/index.html` with `latest_question_list`.
- `polls/models.py` defines domain models:
  - `Question(question_text, pub_date)` and `Choice(question, choice_text, votes)`.
  - `Choice.question` is a FK to `Question` (cascade delete).
- `polls/admin.py` registers `Question` and `Choice` so they appear in the Django admin.

### Templates
- `polls/templates/polls/index.html` renders the list of questions.

### Migrations
- `polls/migrations/0001_initial.py` creates the `Question` and `Choice` tables.

### Deployment entrypoints (not configured here)
- `config/wsgi.py` and `config/asgi.py` provide the WSGI/ASGI `application` for production servers.