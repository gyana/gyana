import uuid

import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK
from apps.dashboards.models import Dashboard

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/projects/{project_id}/dashboards/", id="list"),
        pytest.param("/projects/{project_id}/dashboards/overview", id="overview"),
        pytest.param("/projects/{project_id}/dashboards/new", id="create"),
        pytest.param(
            "/projects/{project_id}/dashboards/create_from_integration",
            id="create_from_integration",
        ),
        pytest.param("/projects/{project_id}/dashboards/{dashboard_id}", id="detail"),
        pytest.param(
            "/projects/{project_id}/dashboards/{dashboard_id}/delete", id="delete"
        ),
        pytest.param(
            "/projects/{project_id}/dashboards/{dashboard_id}/pages/new",
            id="page-create",
        ),
        pytest.param(
            "/projects/{project_id}/dashboards/{dashboard_id}/pages/{page_id}",
            id="page-delete",
        ),
        pytest.param(
            "/projects/{project_id}/dashboards/{dashboard_id}/settings", id="settings"
        ),
        pytest.param("/dashboards/{dashboard_id}/duplicate", id="duplicate"),
        pytest.param("/dashboards/{dashboard_id}/share", id="share"),
    ],
)
def test_project_required(client, url, dashboard_factory, user):
    dashboard = dashboard_factory()
    page = dashboard.pages.create()
    url = url.format(
        project_id=dashboard.project.id, dashboard_id=dashboard.id, page_id=page.id
    )
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    dashboard.project.team = user.teams.first()
    dashboard.project.save()
    r = client.get(url)
    assertOK(r)


def test_public_dashboard(client, dashboard_factory):
    dashboard = dashboard_factory(shared_id=uuid.uuid4())
    dashboard.pages.create()
    r = client.get(f"/dashboards/{dashboard.shared_id}")
    assert r.status_code == 404

    dashboard.shared_status = Dashboard.SharedStatus.PUBLIC
    dashboard.save()
    r = client.get(f"/dashboards/{dashboard.shared_id}")
    assertOK(r)


@pytest.mark.parametrize(
    "url, success_code",
    [
        pytest.param("/dashboards/{}/login", 200, id="login"),
        pytest.param("/dashboards/{}/logout", 302, id="logout"),
    ],
)
def test_password_protected(client, url, success_code, dashboard_factory):
    dashboard = dashboard_factory(shared_id=uuid.uuid4())
    dashboard.pages.create()

    url = url.format(dashboard.shared_id)
    r = client.get(url)
    assert r.status_code == 404

    dashboard.shared_status = Dashboard.SharedStatus.PASSWORD_PROTECTED
    dashboard.save()
    session = client.session
    session.update({str(dashboard.shared_id): ""})
    session.save()
    r = client.get(url)
    assert r.status_code == success_code
