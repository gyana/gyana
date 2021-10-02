import pytest
from apps.teams.models import Team
from apps.users.models import CustomUser

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
