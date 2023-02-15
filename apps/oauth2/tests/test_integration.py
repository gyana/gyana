from urllib import parse

import pytest
from pytest_django.asserts import assertRedirects

from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
)

pytestmark = pytest.mark.django_db


def test_oauth2_crudl(client, logged_in_user, project_factory, mocker):
    fetch_token = mocker.patch(
        "requests_oauthlib.OAuth2Session.fetch_token",
        return_value={"access_token": "12345"},
    )
    project = project_factory(team=logged_in_user.teams.first())

    # create
    r = client.get_htmx_partial(
        f"/projects/{project.id}/update", f"/projects/{project.id}/oauth2/"
    )
    assertOK(r)
    assertLink(r, f"/projects/{project.id}/oauth2/new", "connect one")

    r = client.post(f"/projects/{project.id}/oauth2/new", data={"name": "Github"})
    assert project.oauth2_set.count() == 1
    oauth2 = project.oauth2_set.first()
    oauth2.name == "Github"

    assertRedirects(
        r, f"/projects/{project.id}/oauth2/{oauth2.id}/update", status_code=303
    )

    # update
    r = client.get(f"/projects/{project.id}/oauth2/{oauth2.id}/update")
    assertOK(r)
    assertFormRenders(
        r,
        [
            "name",
            "client_id",
            "client_secret",
            "authorization_base_url",
            "token_url",
            "scope",
        ],
    )

    r = client.post(
        f"/projects/{project.id}/oauth2/{oauth2.id}/update",
        data={
            "name": "Github",
            "client_id": "client_id",
            "client_secret": "client_secret",
            "authorization_base_url": "https://authorize.url",
            "token_url": "https://token.url",
            "scope": "repo",
        },
    )
    assertRedirects(
        r, f"/oauth2/{oauth2.id}/login", status_code=303, target_status_code=302
    )

    # oauth2 login
    r = client.get(f"/oauth2/{oauth2.id}/login")
    oauth2.refresh_from_db()
    authorization_url = f"https://authorize.url?response_type=code&client_id=client_id&redirect_uri={parse.quote(oauth2.callback_url)}&scope=repo&state={oauth2.state}"
    assertRedirects(
        r, authorization_url, status_code=302, fetch_redirect_response=False
    )

    assert oauth2.token is None
    assert fetch_token.call_count == 0

    # oauth callback
    mock_code = "1234567890"
    r = client.get(
        f"/oauth2/{oauth2.id}/callback?code={mock_code}&state={oauth2.state}"
    )
    assertRedirects(r, f"/projects/{project.id}/update")

    oauth2.refresh_from_db()
    assert oauth2.token == {"access_token": "12345"}

    assert fetch_token.call_count == 1
    assert fetch_token.call_args.args == (oauth2.token_url,)
    assert fetch_token.call_args.kwargs == {
        "client_secret": oauth2.client_secret,
        "authorization_response": f"http://testserver/oauth2/1/callback?code={mock_code}&state={oauth2.state}",
    }

    # list
    r = client.get_htmx_partial(
        f"/projects/{project.id}/update", f"/projects/{project.id}/oauth2/"
    )
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 1)
    assertLink(
        r, f"/projects/{project.id}/oauth2/{oauth2.id}/delete", title="Delete OAuth2"
    )

    # delete
    r = client.get(f"/projects/{project.id}/oauth2/{oauth2.id}/delete")
    assertOK(r)
    assertFormRenders(r)

    r = client.delete(f"/projects/{project.id}/oauth2/{oauth2.id}/delete")
    assertRedirects(r, f"/projects/{project.id}/update")

    assert project.oauth2_set.count() == 0
