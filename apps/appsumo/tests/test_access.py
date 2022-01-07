import pytest

from apps.appsumo.models import AppsumoCode

pytestmark = pytest.mark.django_db

CODE = "12345678"


@pytest.mark.parametrize(
    "url, status_code",
    [
        pytest.param("/appsumo", 301, id="landing"),
        pytest.param(f"/appsumo/{CODE}", 302, id="redirect"),
        pytest.param(f"/appsumo/signup/{CODE}", 200, id="signup"),
    ],
)
def test_no_login_required(client, url, status_code):
    AppsumoCode(code=CODE).save()

    r = client.get(url)
    assert r.status_code == status_code


def test_login_required(client, user):

    AppsumoCode(code=CODE).save()

    r = client.get(f"/appsumo/redeem/{CODE}")
    assert r.status_code == 302
    assert r.url == f"/login/?next=/appsumo/redeem/{CODE}"

    client.force_login(user)
    r = client.get(f"/appsumo/redeem/{CODE}")
    assert r.status_code == 200


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("appsumo/", id="list"),
        pytest.param("appsumo/stack", id="stack"),
        pytest.param("appsumo/extra", id="extra"),
    ],
)
def test_admin_required(client, user, url):
    AppsumoCode(code=CODE).save()
    team = user.teams.first()
    url = f"/teams/{team.id}/{url}"

    r = client.get(url)
    assert r.status_code == 302
    assert r.url == f"/login/?next={url}"

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    membership = user.membership_set.first()
    membership.role = "admin"
    membership.save()

    r = client.get(url)
    assert r.status_code == 200
