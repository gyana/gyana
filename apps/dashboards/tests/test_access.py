import uuid

import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK
from apps.dashboards.models import Dashboard

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/dashboards/{}/duplicate", id="duplicate"),
        pytest.param("/dashboards/{}/share", id="share"),
    ],
)
def test_dashboard_required(client, url, dashboard_factory, user):
    dashboard = dashboard_factory()
    assertLoginRedirect(client, url.format(dashboard.id))

    client.force_login(user)
    r = client.get(url.format(dashboard.id))
    assert r.status_code == 404

    user_dashboard = dashboard_factory(project__team=user.teams.first())
    r = client.get(url.format(user_dashboard.id))
    assertOK(r)


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
    ],
)
def test_project_required(client, url, dashboard_factory, user):
    dashboard = dashboard_factory()
    page = dashboard.pages.create()
    first_url = url.format(
        project_id=dashboard.project.id, dashboard_id=dashboard.id, page_id=page.id
    )
    assertLoginRedirect(client, first_url)

    client.force_login(user)
    r = client.get(first_url)
    assert r.status_code == 404

    user_dashboard = dashboard_factory(project__team=user.teams.first())
    page = user_dashboard.pages.create()
    r = client.get(
        url.format(
            project_id=user_dashboard.project.id,
            dashboard_id=user_dashboard.id,
            page_id=page.id,
        )
    )
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
