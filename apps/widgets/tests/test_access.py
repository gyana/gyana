import uuid

import pytest
from django.utils import timezone

from apps.base.tests.asserts import assertLoginRedirect, assertOK
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import mock_bq_client_with_schema
from apps.dashboards.models import Dashboard

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param(
            "/projects/{project_id}/dashboards/{dashboard_id}/widgets/new", id="new"
        ),
        pytest.param("/widgets/{widget_id}/name", id="name"),
        pytest.param(
            "/projects/{project_id}/dashboards/{dashboard_id}/widgets/{widget_id}",
            id="detail",
        ),
        pytest.param(
            "/projects/{project_id}/dashboards/{dashboard_id}/widgets/{widget_id}/delete",
            id="delete",
        ),
        pytest.param(
            "/projects/{project_id}/dashboards/{dashboard_id}/widgets/{widget_id}/update",
            id="update",
        ),
        pytest.param(
            "/projects/{project_id}/dashboards/{dashboard_id}/widgets/{widget_id}/update-style",
            id="update-style",
        ),
    ],
)
def test_widget_project_required(client, url, user, widget_factory, bigquery):
    mock_bq_client_with_schema(
        bigquery, [(name, type_.name) for name, type_ in TABLE.schema().items()]
    )
    widget = widget_factory()
    project = widget.page.dashboard.project
    url = url.format(
        project_id=project.id,
        dashboard_id=widget.page.dashboard.id,
        widget_id=widget.id,
    )
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    project.team = user.teams.first()
    project.save()
    r = client.get(url)
    assertOK(r)


def test_widget_output(client, user, widget_factory):
    widget = widget_factory(page__dashboard__shared_id=uuid.uuid4())
    dashboard = widget.page.dashboard
    url = f"/projects/{dashboard.project.id}/dashboards/{dashboard.id}/widgets/{widget.id}/output"
    r = client.get(url)
    assert r.status_code == 404

    dashboard.shared_status = Dashboard.SharedStatus.PUBLIC
    dashboard.save()
    r = client.get(url)
    assertOK(r)

    dashboard.shared_status = Dashboard.SharedStatus.PASSWORD_PROTECTED
    dashboard.password = "test"
    dashboard.password_set = timezone.now()
    dashboard.save()

    r = client.get(url)
    assert r.status_code == 404

    session = client.session
    session.update(
        {
            str(dashboard.shared_id): {
                "logged_in": timezone.now().isoformat(),
                "auth_success": True,
            }
        }
    )
    session.save()
    r = client.get(url)
    assertOK(r)

    dashboard.shared_status = Dashboard.SharedStatus.PRIVATE
    dashboard.save()
    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    dashboard.project.team = user.teams.first()
    dashboard.project.save()

    r = client.get(url)
    assertOK(r)
