# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (requires SECRET_KEY env var, or set DEBUG=True for auto-key)
DEBUG=True python manage.py runserver

# Apply DB migrations after schema changes
python manage.py migrate

# Make migrations after editing recipes/models.py
python manage.py makemigrations

# Django system check
python manage.py check
```

There is no test suite configured.

Environment variables: `SECRET_KEY` (required in production), `DATABASE_URL` (defaults to SQLite at `db.sqlite3`), `DEBUG`, `ALLOWED_HOSTS`.

## Architecture

Django 4.2 recipe management app. Single `recipes` app handles all features. No JavaScript framework — Django templates + vanilla JS + Tailwind CSS (CDN).

### URL → view → template

All routes are in `recipe_saver/urls.py`. Views are function-based in `recipes/views.py`. Templates live in `templates/` (not inside the app).

- `/login`, `/register`, `/logout` — unauthenticated views
- `/recipes/` — list with search (`?q=`) and tag filter (`?tag=<id>`)
- `/recipes/new/`, `/recipes/<pk>/edit/` — share `templates/recipes/form.html` and `_form_context()`
- `/api/scrape/` and `/api/tags/` — JSON endpoints called by client-side JS on the form page

### Data model

Four models in `recipes/models.py`: Django's built-in `User`, `Tag` (name + hex color, unique per user), `Recipe` (title, source_url, thumbnail, description, ingredients, steps, notes, rating 1–5). Ingredients and steps are `JSONField` arrays of strings. `Recipe.tags` is a ManyToMany to `Tag`. No junction model — Django manages it.

`User.email` is used as the login identifier; `User.username` is set to the email on registration.

### Form page complexity

`templates/recipes/form.html` is the most complex file. Ingredients, steps, rating, and tags are not standard HTML form fields — they are managed entirely in client-side JS arrays and serialized into hidden `<input>` fields on submit (`ingredients_json`, `steps_json`, `rating`, `tag_ids`). The view reads these hidden fields directly from `request.POST`, bypassing the `RecipeForm` model form (which only covers `title`, `description`, `source_url`, `thumbnail`, `notes`). See `_apply_recipe_post()` in `views.py` for where those fields are saved.

### Context processor

`recipes/context_processors.py` injects `sidebar_tags` (all tags for the current user) into every template. This runs an extra DB query on every authenticated page load.

### Auth

Session-based auth via Django's built-in `django.contrib.auth`. Login looks up by email → fetches username → calls `authenticate()`. Password validation enforces 8-char minimum, common password check, numeric-only check, and similarity check (configured in `settings.py`).

### SSRF protection

`_check_url_safe()` in `views.py` validates scrape URLs using `socket.getaddrinfo` (checks all resolved IPs including IPv6) before fetching. The scrape response is capped at 2MB.

### Deployment

Docker + Gunicorn + WhiteNoise for static files. See `Dockerfile` and `fly.toml`. PostgreSQL is used in production via `DATABASE_URL`; SQLite is the default for local dev.
