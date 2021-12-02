import pytest
import pytz
from pytest_django.asserts import assertRedirects

from .mock import get_mock_fivetran_connector

pytestmark = pytest.mark.django_db


def test_connector_schedule(client, logged_in_user, fivetran, connector_factory):

    team = logged_in_user.teams.first()
    connector = connector_factory(integration__project__team=team)
    integration = connector.integration
    project = integration.project
    fivetran.get.return_value = get_mock_fivetran_connector(daily_sync_time="03:00")

    # +05:30 GMT with no daylight savings (testing is easier)
    team.timezone = pytz.timezone("Asia/Kolkata")
    team.save()

    # update the daily sync time in a project via UI
    r = client.post(
        f"/projects/{project.id}/update",
        data={
            "name": "KPIs",
            "description": "All the company kpis",
            "access": "everyone",
            "daily_schedule_time": "09:00",
            "submit": True,
        },
    )
    assertRedirects(r, f"/projects/{project.id}/update", status_code=303)

    project.refresh_from_db()
    connector.refresh_from_db()

    assert project.daily_schedule_time.strftime("%H:%M") == "09:00"
    # test logic for 30 minute offset as well
    assert connector.daily_sync_time == "03:00"
    assert fivetran.update.call_count == 1
    # the UTC time, given Kolkata is +05:30, rounded down to nearest hour
    assert fivetran.update.call_args.args == (connector,)
    assert fivetran.update.call_args.kwargs == {"daily_sync_time": "03:00"}

    # update the timezone in a team via UI
    fivetran.get.return_value = get_mock_fivetran_connector(daily_sync_time="01:00")
    # +08:00 GMT with no daylight savings
    r = client.post(
        f"/teams/{team.id}/update",
        data={"name": "Team", "timezone": "Asia/Shanghai"},
    )
    assertRedirects(r, f"/teams/{team.id}/update", status_code=303)

    project.refresh_from_db()
    connector.refresh_from_db()

    assert connector.daily_sync_time == "01:00"
    assert fivetran.update.call_count == 2
    # the UTC time, given Beijing is +08:00, rounded down to nearest hour
    assert fivetran.update.call_args.args == (connector,)
    assert fivetran.update.call_args.kwargs == {"daily_sync_time": "01:00"}
