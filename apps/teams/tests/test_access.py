import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK
from apps.teams import roles

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/teams/{team_id}/update", id="update"),
        pytest.param("/teams/{team_id}/delete", id="delete"),
    ],
)
def test_admin_required(client, user, url, team_factory, settings):
    team = team_factory()

    url = url.format(team_id=team.id)
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    team.members.add(user)
    r = client.get(url)
    assert r.status_code == 404

    membership = user.membership_set.first()
    membership.role = roles.ROLE_ADMIN
    membership.save()

    r = client.get(url)
    assertOK(r)


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/teams/{team_id}/members/", id="list"),
        pytest.param("/teams/{team_id}/members/{membership_id}/update", id="update"),
        pytest.param("/teams/{team_id}/members/{membership_id}/delete", id="delete"),
    ],
)
def test_membership(client, user, url, team_factory):
    team = team_factory()
    team.members.add(user)
    membership = user.membership_set.first()
    url = url.format(team_id=team.id, membership_id=membership.id)
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    membership.role = roles.ROLE_ADMIN
    membership.save()

    r = client.get(url)
    assertOK(r)
