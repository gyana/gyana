import re

import pytest
from django.core import mail
from pytest_django.asserts import assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertLink, assertOK
from apps.users.models import CustomUser

pytestmark = pytest.mark.django_db


def test_login(client):
    CustomUser.objects.create_user(
        "test", email="test@gyana.com", password="seewhatmatters", onboarded=True
    )

    r = client.get("/login/")
    assertOK(r)
    assertFormRenders(r, ["login", "password"])

    r = client.post(
        "/login/", data={"login": "test@gyana.com", "password": "seewhatmatters"}
    )
    assertRedirects(r, "/", status_code=302, target_status_code=302)

    r = client.get("/")
    assertRedirects(r, "/teams/new")


def test_sign_up(client):

    r = client.get("/signup/")
    assertOK(r)
    assertFormRenders(r, ["email", "password1"])

    r = client.post(
        "/signup/", data={"email": "new@gyana.com", "password1": "seewhatmatters"}
    )
    assertRedirects(r, "/", status_code=302, target_status_code=302)

    r = client.get("/")
    assertRedirects(r, "/users/onboarding/")


def test_reset_password(client):
    CustomUser.objects.create_user(
        "test", email="test@gyana.com", password="seewhatmatters", onboarded=True
    )

    # request reset
    r = client.get("/login/")
    assertOK(r)
    assertLink(r, "/password/reset/", "Forgot your password?")

    r = client.get("/password/reset/")
    assertOK(r)
    assertFormRenders(r, ["email"])

    r = client.post("/password/reset/", data={"email": "test@gyana.com"})
    assertRedirects(r, "/password/reset/done/", status_code=302)

    assert len(mail.outbox) == 1
    link = re.search("(?P<url>https?://[^\s]+)", mail.outbox[0].body).group("url")

    # change password
    r = client.get(link)
    assert r.status_code == 302
    set_password_url = r.url
    assert re.match(
        r"^\/password\/reset\/key\/[a-zA-Z0-9]+-set-password\/$", set_password_url
    )

    r = client.get(set_password_url)
    assertOK(r)
    assertFormRenders(r, ["password1", "password2"])

    r = client.post(
        set_password_url,
        data={"password1": "senseknowdecide", "password2": "senseknowdecide"},
    )
    assertRedirects(r, "/password/reset/key/done/", status_code=302)

    # login
    r = client.post(
        "/login/", data={"login": "test@gyana.com", "password": "senseknowdecide"}
    )
    assertRedirects(r, "/", status_code=302, target_status_code=302)
    assertRedirects(client.get("/"), "/teams/new")


def test_sign_out(client, logged_in_user):
    team = logged_in_user.teams.first()

    # logged in
    r = client.get("/")
    assertRedirects(r, f"/teams/{team.id}")

    # Test logout link exists
    r = client.get(f"/teams/{team.id}")
    assertOK(r)
    assertLink(r, "/logout/", "Sign out")

    # logout
    r = client.get("/logout/")
    assertRedirects(r, "/login/")
