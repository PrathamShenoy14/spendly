import pytest
from flask import url_for

import database.db as db

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"


def login(client, **overrides):
    data = {"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
    data.update(overrides)
    return client.post("/login", data=data)


def demo_id():
    return db.get_user_by_email(DEMO_EMAIL)["id"]


def session_data(client):
    with client.session_transaction() as sess:
        return dict(sess)


def set_logged_in(client, user_id=1):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def test_app_has_secret_key(app):
    assert app.secret_key


def test_login_page_renders(app, client):
    resp = client.get("/login")
    assert resp.status_code == 200
    with app.test_request_context():
        expected = url_for("login")
    assert f'action="{expected}"'.encode() in resp.data


def test_login_success_redirects_to_profile(client):
    resp = login(client)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")
    assert session_data(client)["user_id"] == demo_id()


def test_login_email_normalised(client):
    resp = login(client, email="  DEMO@Spendly.com ")
    assert resp.status_code == 302
    assert session_data(client)["user_id"] == demo_id()


def test_login_wrong_password(client):
    resp = login(client, password="wrongpass1")
    assert resp.status_code == 400
    assert b"Invalid email or password." in resp.data
    assert "user_id" not in session_data(client)


def test_login_unknown_email_same_error(client):
    resp = login(client, email="nobody@example.com")
    assert resp.status_code == 400
    assert b"Invalid email or password." in resp.data
    assert "user_id" not in session_data(client)


@pytest.mark.parametrize(
    "data",
    [
        {"email": "", "password": DEMO_PASSWORD},
        {"email": DEMO_EMAIL, "password": ""},
        {"email": "", "password": ""},
        {},
    ],
)
def test_login_missing_fields(client, data):
    resp = client.post("/login", data=data)
    assert resp.status_code == 400
    assert b"auth-error" in resp.data
    assert "user_id" not in session_data(client)


def test_login_failure_preserves_email_not_password(client):
    resp = login(client, password="wrongpass1")
    body = resp.data.decode()
    assert f'value="{DEMO_EMAIL}"' in body
    assert "wrongpass1" not in body
    assert "value" not in body.split('id="password"')[1].split(">")[0]


def test_session_contains_only_user_id(client):
    login(client)
    assert set(session_data(client)) == {"user_id"}


def test_login_discards_previous_session_data(client):
    with client.session_transaction() as sess:
        sess["stale"] = "x"
    login(client)
    assert set(session_data(client)) == {"user_id"}


def test_logout_clears_session_and_redirects(client):
    login(client)
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")
    assert session_data(client) == {}


def test_logout_when_logged_out(client):
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_navbar_logged_out(client):
    body = client.get("/").data.decode()
    assert ">Sign in<" in body
    assert ">Get started<" in body
    assert ">Sign out<" not in body


def test_navbar_after_logout(client):
    login(client)
    client.get("/logout")
    body = client.get("/").data.decode()
    assert ">Sign in<" in body
    assert ">Sign out<" not in body


def test_navbar_logged_in(client):
    set_logged_in(client)
    body = client.get("/").data.decode()
    assert ">Sign out<" in body
    assert ">Profile<" in body
    assert ">Get started<" not in body
    assert ">Sign in<" not in body


@pytest.mark.parametrize("path", ["/login", "/register"])
def test_logged_in_get_redirects_to_profile(client, path):
    set_logged_in(client)
    resp = client.get(path)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")


def test_register_then_login(client):
    client.post(
        "/register",
        data={
            "name": "New Person",
            "email": "new@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    resp = login(client, email="new@example.com", password="password123")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")


def test_password_never_in_response_body(client):
    resp = login(client, password="wrongpass1")
    assert b"wrongpass1" not in resp.data
