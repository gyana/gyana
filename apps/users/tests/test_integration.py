import re

import pytest
from apps.teams.models import Team
from apps.users.models import CustomUser
from django.core import mail

pytestmark = pytest.mark.django_db


def test_login(client):
    CustomUser.objects.create_user(
        "test", email="test@gyana.com", password="seewhatmatters", onboarded=True
    )

    r = client.get("/")
    assert r.status_code == 302
    assert r.url == "/login/"

    assert client.get("/login/").status_code == 200

    r = client.post(
        "/login/", data={"login": "test@gyana.com", "password": "seewhatmatters"}
    )
    assert r.status_code == 303
    assert r.url == "/"


def test_sign_up_with_onboarding(client):

    assert client.get("/signup/").status_code == 200

    # todo: migrate onboarding logic here when signup is enabled


def test_reset_password(client):
    CustomUser.objects.create_user(
        "test", email="test@gyana.com", password="seewhatmatters", onboarded=True
    )

    # request reset
    assert client.get("/password/reset/").status_code == 200

    r = client.post("/password/reset/", data={"email": "test@gyana.com"})
    assert r.status_code == 303
    assert r.url == "/password/reset/done/"

    assert len(mail.outbox) == 1
    link = re.search("(?P<url>https?://[^\s]+)", mail.outbox[0].body).group("url")

    # change password
    r = client.get(link)
    assert r.status_code == 302
    assert re.match(r"^\/password\/reset\/key\/[a-zA-Z0-9]-set-password\/$", r.url)

    assert client.get(r.url).status_code == 200

    r = client.post(
        r.url, data={"password1": "senseknowdecide", "password2": "senseknowdecide"}
    )
    assert r.status_code == 303
    assert r.url == "/password/reset/key/done/"

    # login
    r = client.post(
        "/login/", data={"login": "test@gyana.com", "password": "senseknowdecide"}
    )
    assert r.status_code == 303
    assert r.url == "/"


def test_sign_out(client, logged_in_user):
    team = logged_in_user.teams.first()

    # logged in
    r = client.get("/")
    assert r.status_code == 302
    assert r.url == f"/teams/{team.id}"

    # logout
    r = client.get("/logout/")
    assert r.status_code == 302
    assert r.url == "/"

    r = client.get("/")
    assert r.status_code == 302
    assert r.url == "/login/"
