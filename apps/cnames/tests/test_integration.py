import pytest
from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
)
from pytest_django.asserts import assertContains, assertRedirects

pytestmark = pytest.mark.django_db


def test_cname_crudl(client, logged_in_user, heroku):
    team = logged_in_user.teams.first()

    heroku.get_domain().acm_status = "waiting"
    heroku.reset_mock()

    # create
    r = client.get_turbo_frame(f"/teams/{team.id}/update", f"/teams/{team.id}/cnames/")
    assertOK(r)
    assertLink(r, f"/teams/{team.id}/cnames/new", "create one")

    r = client.get(f"/teams/{team.id}/cnames/new")
    assertOK(r)
    assertFormRenders(r, ["domain"])

    r = client.post(f"/teams/{team.id}/cnames/new", data={"domain": "test.domain.com"})
    assertRedirects(r, f"/teams/{team.id}/update", status_code=303)

    assert team.cname_set.count() == 1
    cname = team.cname_set.first()
    cname.domain == "test.domain.com"
    assert heroku.add_domain.call_count == 1
    assert heroku.add_domain.call_args.args == ("test.domain.com",)

    # read and update not enabled

    # list
    r = client.get_turbo_frame(f"/teams/{team.id}/update", f"/teams/{team.id}/cnames/")
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 1)
    assertLink(r, f"/teams/{team.id}/cnames/{cname.id}/delete", title="Delete CNAME")

    # status indicator
    r = client.get_turbo_frame(
        f"/teams/{team.id}/update",
        f"/teams/{team.id}/cnames/",
        f"/cnames/{cname.id}/status",
    )
    assertSelectorLength(r, ".fa-spinner-third", 1)
    assert heroku.get_domain.call_count == 1
    assert heroku.get_domain.call_args.args == ("test.domain.com",)

    heroku.get_domain().acm_status = "cert issued"
    heroku.reset_mock()
    r = client.get_turbo_frame(
        f"/teams/{team.id}/update",
        f"/teams/{team.id}/cnames/",
        f"/cnames/{cname.id}/status",
    )
    assertOK(r)
    assertSelectorLength(r, ".fa-check", 1)
    assert heroku.get_domain.call_count == 1
    assert heroku.get_domain.call_args.args == ("test.domain.com",)

    # delete
    heroku.reset_mock()
    r = client.get(f"/teams/{team.id}/cnames/{cname.id}/delete")
    assertOK(r)
    assertFormRenders(r)

    r = client.delete(f"/teams/{team.id}/cnames/{cname.id}/delete")
    assertRedirects(r, f"/teams/{team.id}/update")

    assert team.cname_set.count() == 0
    assert heroku.get_domain.call_count == 1
    assert heroku.get_domain.call_args.args == ("test.domain.com",)
    assert heroku.get_domain().remove.call_count == 1
