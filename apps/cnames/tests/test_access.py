import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertNotFound, assertOK

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/cnames/{cname_id}/status", id="status"),
        pytest.param("/teams/{team_id}/cnames/", id="list"),
        pytest.param("/teams/{team_id}/cnames/new", id="create"),
        pytest.param("/teams/{team_id}/cnames/{cname_id}/delete", id="delete"),
    ],
)
def test_access(client, url, user, c_name_factory, heroku):
    heroku.get_domain().acm_status = "waiting"
    heroku.reset_mock()
    cname = c_name_factory()
    first_url = url.format(team_id=cname.team.id, cname_id=cname.id)
    assertLoginRedirect(client, first_url)

    client.force_login(user)
    r = client.get(first_url)
    assertNotFound(r)

    cname.team = user.teams.first()
    cname.save()
    r = client.get(url.format(team_id=cname.team.id, cname_id=cname.id))
    assertOK(r)
