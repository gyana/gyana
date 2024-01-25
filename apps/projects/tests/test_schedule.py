import json
from uuid import uuid4

import pytest
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from pytest_django.asserts import assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertOK
from apps.projects import periodic
from apps.runs.models import GraphRun

pytestmark = pytest.mark.django_db


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
    assertFormRenders(
        r, ["cell_range", "sheet_name", "is_scheduled"], "#integration-schedule-form"
    )

    # Add the schedule
    r = client.post(f"{DETAIL}/settings", data={"is_scheduled": True})
    assertRedirects(r, f"{DETAIL}/load", status_code=302)

    sheet.refresh_from_db()
    assert sheet.integration.is_scheduled

    project.refresh_from_db()
    assert project.periodic_task is not None
    periodic_task = project.periodic_task
    assert periodic_task.task == "apps.projects.periodic.run_schedule_for_project"
    assert json.loads(periodic_task.args) == [project.id]
    assert periodic_task.crontab.hour == str(project.daily_schedule_time.hour)
    assert periodic_task.crontab.timezone == team.timezone

    # Update the timezone
    r = client.post(
        f"/teams/{team.id}/update",
        data={"name": "Team", "timezone": "Asia/Shanghai", "beta": False},
    )
    assertRedirects(r, f"/teams/{team.id}/update", status_code=303)

    periodic_task.refresh_from_db()
    assert str(periodic_task.crontab.timezone) == "Asia/Shanghai"

    # Remove the schedule
    r = client.post(f"{DETAIL}/settings", data={"is_scheduled": False})
    assertRedirects(r, f"{DETAIL}/settings", status_code=302)

    project.refresh_from_db()
    assert project.periodic_task is None
    assert PeriodicTask.objects.count() == 0
    assert CrontabSchedule.objects.count() == 0


def test_run_schedule_for_periodic(project_factory, sheet_factory, mocker):
    mocker.patch("apps.projects.tasks.run_project_task")

    project = project_factory()
    sheet = sheet_factory(integration__project=project, integration__is_scheduled=True)

    project.update_schedule()

    assert project.periodic_task is not None

    task_id = str(uuid4())

    # TODO: What to do with this after connector removal
    # with pytest.raises(RetryTaskError):
    #     periodic.run_schedule_for_project.apply_async((project.id,), task_id=task_id)

    # assert project.runs.count() == 1
    # graph_run = project.runs.first()
    # assert graph_run.state == GraphRun.State.RUNNING

    periodic.run_schedule_for_project.apply_async((project.id,), task_id=task_id)
    graph_run = project.runs.first()
    assert project.runs.count() == 1
    graph_run.refresh_from_db()
    assert graph_run.state == GraphRun.State.SUCCESS
