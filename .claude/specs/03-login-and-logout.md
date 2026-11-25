# Spec: Login and Logout

## Overview
Let a registered user sign in and out. `POST /login` checks the submitted email and password against the `users` table and, on success, stores the user's id in Flask's signed session cookie. `GET /logout` clears the session. This is the second half of authentication: Step 2 created accounts, and every later step (profile, expense add/edit/delete) needs to know who is making the request. This step also introduces the app's `secret_key`, which Step 2 deliberately left out.

## Depends on
- Step 01 — Database setup (`users` table, `get_db()`)
- Step 02 — Registration (`get_user_by_email()`, users with werkzeug-hashed passwords, redirect to `login` after registering)

## Routes
- GET /login — render the sign-in form (already implemented); if already logged in, redirect to `profile` — public
- POST /login — validate credentials; on success set `session["user_id"]` and redirect to `profile`; on failure re-render `login.html` with an `error` and HTTP 400 — public
- GET /register — if already logged in, redirect to `profile`; otherwise unchanged — public
- GET /logout — clear the session and redirect to `landing` — logged-in (a logged-out visitor is simply redirected to `landing` as well, with no error)

`profile` is still a stub (Step 4) and returns a plain string. Landing on it after login is expected until Step 4; do not implement it.

## Database changes
No database changes. The existing `users` table has everything needed (`id`, `email`, `password_hash`). Reuse `get_user_by_email()` from `database/db.py`. If a lookup by id is needed for the navbar or later steps, add `get_user_by_id(user_id)` to `database/db.py`, parameterised, mirroring `get_user_by_email()`.

## Templates
- Create: none
- Modify:
  - `templates/login.html` — change `action="/login"` to `action="{{ url_for('login') }}"`; re-fill the `email` input from the submitted value after an error (never re-fill the password)
  - `templates/base.html` — make the navbar depend on `session.get("user_id")`: when logged in, show a "Sign out" link using `url_for('logout')` (and a link to `url_for('profile')`); when logged out, keep the existing "Sign in" and "Get started" links

## Files to change
- `app.py` — set `app.secret_key`; make `/login` accept GET and POST with the credential check; implement `/logout`; add the logged-in redirect to `/register`
- `database/db.py` — only if `get_user_by_id()` is needed
- `templates/login.html` — `url_for` action, preserve email on error
- `templates/base.html` — conditional navbar links
- `CLAUDE.md` — update the routes table (`POST /register`, `POST /login` and `GET /logout` implemented) and remove the stale "db.py is empty" note

## Files to create
- `tests/test_login_logout.py` — pytest tests for the behaviour in the Definition of done

## New dependencies
No new dependencies. `session` is part of Flask and password checking uses `werkzeug.security.check_password_hash`.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug: verify with `check_password_hash`, never compare plaintext, never log passwords
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No DB logic in route functions; use the helpers in `database/db.py`
- Use `url_for()` for every internal link and redirect — never hardcode URLs
- `secret_key` must not be a hardcoded secret for production use: read it from an environment variable (for example `SPENDLY_SECRET_KEY`) and fall back to a clearly labelled development-only default so `python app.py` still starts
- Store only `user_id` in the session — not the email, name or password hash
- Normalise the login email the same way registration does (strip and lowercase) before the lookup
- Use one generic error for every credential failure ("Invalid email or password."), whether the email is unknown or the password is wrong, so the form does not reveal which emails are registered
- Run `check_password_hash` only against a real user row; an unknown email must not raise an error
- Missing form fields re-render the form with an error and HTTP 400 — use `request.form.get(key, "")`, not `request.form[key]`
- Call `session.clear()` on logout, and before setting `user_id` on login, to avoid reusing a stale session
- Do not implement `/profile` or any other stub route; do not add new pip packages; keep the app on port 5001
- Use `abort()` for HTTP errors, not raw string returns

## Definition of done
- [ ] `python app.py` starts on port 5001 with no errors, and the app has a `secret_key`
- [ ] `GET /login` returns 200 and the form action is generated with `url_for('login')`
- [ ] Logging in with a registered email and the correct password redirects (302) to `/profile`, and the session holds that user's `user_id`
- [ ] Email matching is case- and whitespace-insensitive (`  DEMO@Spendly.com ` signs in the demo user)
- [ ] A wrong password re-renders the form with "Invalid email or password." and HTTP 400, and sets no `user_id`
- [ ] An unknown email gets exactly the same error as a wrong password
- [ ] Empty email or empty password re-renders the form with an error and no session
- [ ] After a failed login the email field keeps its value and the password field is empty
- [ ] Only `user_id` is stored in the session
- [ ] `GET /logout` clears the session and redirects (302) to `/`
- [ ] `GET /logout` while logged out redirects to `/` without an error
- [ ] After logout, the navbar shows "Sign in" and "Get started" again, not "Sign out"
- [ ] While logged in, the navbar shows "Sign out", and `/login` and `/register` redirect to `/profile`
- [ ] A user registered through `/register` can immediately sign in with the same credentials
- [ ] `pytest` passes, including the new `tests/test_login_logout.py` and the existing registration tests
