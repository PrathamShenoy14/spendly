import sqlite3

import pytest
from flask import url_for
from werkzeug.security import check_password_hash

import database.db as db


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    db.seed_db()
    from app import app as flask_app

    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def count_users():
    conn = db.get_db()
    try:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        conn.close()


def post_form(client, **overrides):
    data = {"name": "Test User", "email": "new@example.com", "password": "password123"}
    data.update(overrides)
    data.setdefault("confirm_password", data["password"])
    return client.post("/register", data=data)


def test_get_register_renders_form(client):
    resp = client.get("/register")
    assert resp.status_code == 200
    assert b'name="email"' in resp.data


def test_valid_registration_redirects_to_login(client):
    before = count_users()
    resp = post_form(client)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")
    assert count_users() == before + 1


def test_password_is_hashed(client):
    post_form(client)
    user = db.get_user_by_email("new@example.com")
    assert user["password_hash"] != "password123"
    assert check_password_hash(user["password_hash"], "password123")


def test_email_and_name_normalised(client):
    post_form(client, name="  Test User  ", email="  New@Example.COM ")
    user = db.get_user_by_email("new@example.com")
    assert user is not None
    assert user["name"] == "Test User"


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": ""},
        {"name": "   "},
        {"email": ""},
        {"password": ""},
        {"confirm_password": ""},
    ],
)
def test_missing_field_rejected(client, overrides):
    before = count_users()
    resp = post_form(client, **overrides)
    assert resp.status_code == 400
    assert b"auth-error" in resp.data
    assert count_users() == before


def test_missing_form_keys_return_400(client):
    resp = client.post("/register", data={})
    assert resp.status_code == 400


def test_short_password_rejected(client):
    before = count_users()
    resp = post_form(client, password="1234567")
    assert resp.status_code == 400
    assert b"at least 8" in resp.data
    assert count_users() == before


def test_mismatched_passwords_rejected(client):
    before = count_users()
    resp = post_form(client, confirm_password="different123")
    assert resp.status_code == 400
    assert b"do not match" in resp.data
    assert count_users() == before


def test_confirm_password_is_case_sensitive(client):
    resp = post_form(client, confirm_password="PASSWORD123")
    assert resp.status_code == 400
    assert b"do not match" in resp.data


def test_short_password_error_takes_precedence_over_mismatch(client):
    resp = post_form(client, password="short", confirm_password="other")
    assert resp.status_code == 400
    assert b"at least 8" in resp.data


def test_confirm_field_rendered_and_not_echoed(client):
    assert b'name="confirm_password"' in client.get("/register").data
    body = post_form(client, confirm_password="nomatch999").data.decode()
    assert "nomatch999" not in body


def test_eight_char_password_accepted(client):
    assert post_form(client, password="12345678").status_code == 302


@pytest.mark.parametrize(
    "email", ["abc", "a@b", "@b.com", "a@.com", "a@b.", "a b@c.com", "a@@b.com"]
)
def test_invalid_email_rejected(client, email):
    before = count_users()
    resp = post_form(client, email=email)
    assert resp.status_code == 400
    assert b"valid email" in resp.data
    assert count_users() == before


@pytest.mark.parametrize("email", ["demo@spendly.com", "DEMO@Spendly.com"])
def test_duplicate_email_rejected(client, email):
    before = count_users()
    resp = post_form(client, email=email)
    assert resp.status_code == 400
    assert b"already exists" in resp.data
    assert count_users() == before


def test_form_values_preserved_on_error(client):
    resp = post_form(client, password="short")
    body = resp.data.decode()
    assert 'value="Test User"' in body
    assert 'value="new@example.com"' in body
    assert "short" not in body.split('id="password"')[1].split(">")[0]


def test_form_action_uses_register_url(app, client):
    with app.test_request_context():
        expected = url_for("register")
    assert f'action="{expected}"'.encode() in client.get("/register").data


def test_integrity_error_race_returns_400(client, monkeypatch):
    monkeypatch.setattr("app.get_user_by_email", lambda email: None)
    before = count_users()
    resp = post_form(client, email="demo@spendly.com")
    assert resp.status_code == 400
    assert b"already exists" in resp.data
    assert count_users() == before


def test_no_session_cookie_on_success(client):
    resp = post_form(client)
    assert "Set-Cookie" not in resp.headers


def test_get_user_by_email_unknown_returns_none(app):
    assert db.get_user_by_email("nobody@example.com") is None


def test_create_user_returns_id_and_rejects_duplicate(app):
    uid = db.create_user("A B", "ab@example.com", "password123")
    assert isinstance(uid, int)
    with pytest.raises(sqlite3.IntegrityError):
        db.create_user("A B", "ab@example.com", "password123")
