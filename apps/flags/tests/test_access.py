import pytest

from apps.base.tests.asserts import assertOK
from apps.teams import roles

pytestmark = pytest.mark.django_db


def test_team_flags_access(client, user, team_factory):
    team = team_factory()

    URL = f"/teams/{team.id}/beta"

    client.force_login(user)
    r = client.get(URL)
    assert r.status_code == 404

    team.members.add(user)
    r = client.get(URL)
    assert r.status_code == 404

    membership = user.membership_set.first()
    membership.role = roles.ROLE_ADMIN
    membership.save()

    r = client.get(URL)
    assertOK(r)
