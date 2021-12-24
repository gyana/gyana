import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK
from apps.teams import roles

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/teams/{team_id}/invites/", id="list"),
        pytest.param("/teams/{team_id}/invites/new", id="create"),
        pytest.param("/teams/{team_id}/invites/{invite_id}", id="detail"),
        pytest.param("/teams/{team_id}/invites/{invite_id}/update", id="update"),
        pytest.param("/teams/{team_id}/invites/{invite_id}/delete", id="delete"),
        pytest.param("/teams/{team_id}/invites/{invite_id}/resend", id="resend"),
    ],
)
def test_admin_required(client, url, user, invite_factory):
    team = user.teams.first()
    invite = invite_factory(team=team)

    url = url.format(invite_id=invite.id, team_id=team.id)
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    membership = user.membership_set.first()
    membership.role = roles.ROLE_ADMIN
    membership.save()

    r = client.get(url)
    assertOK(r)
