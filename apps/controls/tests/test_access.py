import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param(
            "/projects/{project_id}/dashboards/{dashboard_id}/controls/new", id="create"
        ),
        pytest.param(
            "/projects/{project_id}/dashboards/{dashboard_id}/controls/{control_id}/update",
            id="update",
        ),
        pytest.param(
            "/projects/{project_id}/dashboards/{dashboard_id}/controls/{control_widget_id}/delete",
            id="delete",
        ),
    ],
)
def test_control_widget_project_required(
    client, user, control_widget_factory, url, dashboard_factory
):
    dashboard = dashboard_factory()
    page = dashboard.pages.create()
    control_widget = control_widget_factory(control__page=page, page=page)
    url = url.format(
        project_id=dashboard.project.id,
        dashboard_id=dashboard.id,
        control_id=control_widget.control.id,
        control_widget_id=control_widget.id,
    )
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    dashboard.project.team = user.teams.first()
    dashboard.project.save()
    r = client.get(url)
    assertOK(r)
