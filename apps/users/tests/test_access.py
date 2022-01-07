import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/users/onboarding/", id="onboarding"),
        pytest.param("/users/profile", id="profile"),
    ],
)
def test_login_required(client, url, user):
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assertOK(r)


def test_feedback(client, user, settings):
    settings.HELLONEXT_SSO_TOKEN = "token"
    url = "/users/feedback?domain=test&redirect=test"
    r = client.get(url)
    assert r.status_code == 302

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 302
