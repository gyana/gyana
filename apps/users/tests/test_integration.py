import re

import pytest
from django.core import mail
from pytest_django.asserts import assertContains, assertFormError, assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertLink, assertOK
from apps.users.models import ApprovedWaitlistEmail, CustomUser

pytestmark = pytest.mark.django_db


def test_login(client):
    CustomUser.objects.create_user(
        "test", email="test@gyana.com", password="seewhatmatters", onboarded=True
    )

    assertRedirects(client.get("/"), "/login/")

    r = client.get("/login/")
    assertOK(r)
    assertFormRenders(r, ["login", "password"])

    r = client.post(
        "/login/", data={"login": "test@gyana.com", "password": "seewhatmatters"}
    )
    assertRedirects(r, "/", status_code=303, target_status_code=302)

    r = client.get("/")
    assertRedirects(r, "/teams/new")


def test_sign_up_with_waitlist_approval(client):

    r = client.get("/signup/")
    assertOK(r)
    assertFormRenders(r, ["email", "password1"])

    r = client.post(
        "/signup/", data={"email": "waitlist@gyana.com", "password1": "seewhatmatters"}
    )
    ERROR = 'Gyana is currently invite only. <a href="https://www.gyana.com" class="link">Join our waitlist.</a>'
    assertFormError(r, "form", None, ERROR)

    ApprovedWaitlistEmail.objects.create(email="waitlist@gyana.com")

    r = client.post(
        "/signup/", data={"email": "waitlist@gyana.com", "password1": "seewhatmatters"}
    )
    assertRedirects(r, "/", status_code=303, target_status_code=302)

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
    assertRedirects(r, "/password/reset/done/", status_code=303)

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
    assertRedirects(r, "/password/reset/key/done/", status_code=303)

    # login
    r = client.post(
        "/login/", data={"login": "test@gyana.com", "password": "senseknowdecide"}
    )
    assertRedirects(r, "/", status_code=303, target_status_code=302)
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
    assertRedirects(r, "/", target_status_code=302)

    r = client.get("/")
    assertRedirects(r, "/login/")
