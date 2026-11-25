# Spec: Registration

## Overview
Implement account creation. `GET /register` already renders the form; this step adds `POST /register` so a visitor can submit name, email and password, have the input validated, and get a new row in `users` with a werkzeug-hashed password. It is the first half of authentication and must exist before login (Step 3) can have anyone to sign in. Registration does not log the user in: sessions arrive with login.

## Depends on
- Step 01 — Database setup (`users` table, `get_db()`, `init_db()`).

## Routes
- GET /register — render the registration form (already implemented, unchanged) — public
- POST /register — validate the form, create the user, redirect to `login` on success; re-render `register.html` with an `error` message and HTTP 400 on failure — public

## Database changes
No database changes. The existing `users` table already has `name`, `email` (UNIQUE), `password_hash` and `created_at`.

New helper functions in `database/db.py` (DB logic must not live in routes):
- `get_user_by_email(email)` — returns the matching `sqlite3.Row` or `None`
- `create_user(name, email, password)` — hashes the password with `generate_password_hash`, inserts the row with a parameterised query, returns the new user id. Raises `sqlite3.IntegrityError` if the email already exists (the UNIQUE constraint is the final guard against races).

## Templates
- Create: none
- Modify:
  - `templates/register.html` — change `action="/register"` to `action="{{ url_for('register') }}"`; re-fill `name` and `email` inputs from submitted values after an error (never re-fill the password)

## Files to change
- `app.py` — extend the `/register` route to accept GET and POST and call the db helpers
- `database/db.py` — add `get_user_by_email()` and `create_user()`
- `templates/register.html` — `url_for` action, preserve name/email on error

## Files to create
- `tests/test_registration.py` — pytest tests for the behaviour in the Definition of done

## New dependencies
No new dependencies (`pytest` and `pytest-flask` are already in `requirements.txt`).

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — no f-strings in SQL
- Passwords hashed with werkzeug (`generate_password_hash`); never store or log plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No DB logic in the route function; the route validates input, calls the helpers, then redirects or renders
- Use `url_for()` for every internal link and redirect — never hardcode URLs
- Do not add a `secret_key`, sessions or flash messages; those belong to Step 3
- Do not implement any other stub route (`/login` POST, `/logout`, `/profile`, expenses)
- Validation, in this order, with a clear message for each failure:
  - name, email, password and confirm_password are all present after `strip()` on name and email
  - email is lowercased and stripped, and has a basic valid shape (contains `@` with text on both sides and a dot in the domain)
  - password is at least 8 characters (matches the form placeholder)
  - `confirm_password` matches `password` exactly (case-sensitive); error "Passwords do not match."
  - email is not already registered (check with `get_user_by_email`, and also catch `sqlite3.IntegrityError`)
- Use `abort()` for HTTP errors, not raw string returns
- Keep the app on port 5001

## Definition of done
- [ ] Visiting `/register` still shows the form (GET returns 200)
- [ ] Submitting a valid name, email and 8+ character password creates a row in `users` and redirects (302) to `/login`
- [ ] The stored `password_hash` is not the plaintext password and passes `check_password_hash`
- [ ] The email is stored lowercased and trimmed
- [ ] Submitting with any field empty re-renders the form with an error and creates no user
- [ ] A password shorter than 8 characters is rejected with an error
- [ ] A confirm password field exists, and a mismatch is rejected with "Passwords do not match." and creates no user
- [ ] An invalid email such as `abc` or `a@b` is rejected with an error
- [ ] Registering an email that already exists (for example `demo@spendly.com`, in any letter case) shows an error and does not create a second row
- [ ] After an error, the name and email fields keep their values and the password field is empty
- [ ] The form `action` is generated with `url_for('register')`
- [ ] `pytest tests/test_registration.py` passes
- [ ] The app starts with `python app.py` on port 5001 with no errors
