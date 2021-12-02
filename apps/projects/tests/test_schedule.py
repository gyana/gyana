import json

import pytest
import pytz
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from pytest_django.asserts import assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertOK
from apps.connectors.tests.mock import get_mock_fivetran_connector
from apps.projects.periodic import run_schedule_for_project

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


def test_sheet_schedule(client, logged_in_user, sheet_factory, mocker):

    team = logged_in_user.teams.first()
    sheet = sheet_factory(integration__project__team=team)
    project = sheet.integration.project
    # an extra sheet to check logic
    sheet_factory(integration__project=project)
    run_sheet_sync_task = mocker.patch("apps.sheets.tasks.run_sheet_sync_task")

    # Enable scheduling for sheets, update time and timezone, and then remove
    # the schedule.

    LIST = f"/projects/{sheet.integration.project.id}/integrations"
    DETAIL = f"{LIST}/{sheet.integration.id}"

    r = client.get(f"{DETAIL}/settings")
    assertOK(r)
    # todo: fix this!
    assertFormRenders(r, ["name", "is_scheduled"])

    # Add the schedule
    r = client.post(f"{DETAIL}/settings", data={"is_scheduled": True})
    assertRedirects(r, f"{DETAIL}/settings")

    sheet.refresh_from_db()
    assert sheet.is_scheduled

    project.refresh_from_db()
    assert project.periodic_task is not None
    periodic_task = project.periodic_task
    assert periodic_task.task == "apps.projects.tasks.run_schedule_for_project"
    assert json.loads(periodic_task.args) == [project.id]
    assert periodic_task.crontab.hour == str(project.daily_schedule_time.hour)
    assert periodic_task.crontab.timezone == team.timezone

    # Update the timezone
    r = client.post(
        f"/teams/{team.id}/update",
        data={"name": "Team", "timezone": "Asia/Shanghai"},
    )
    assertRedirects(r, f"/teams/{team.id}/update", status_code=303)

    periodic_task.refresh_from_db()
    assert str(periodic_task.crontab.timezone) == "Asia/Shanghai"

    # Remove the schedule
    r = client.post(f"{DETAIL}/settings", data={"is_scheduled": False})
    assertRedirects(r, f"{DETAIL}/settings")

    project.refresh_from_db()
    assert project.periodic_task is None
    assert PeriodicTask.objects.count() == 0
    assert CrontabSchedule.objects.count() == 0
