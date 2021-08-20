from apps.tables.models import Table
from celery.app import shared_task
from django.db import models, transaction

from .models import Team

WARNING_BUFFER = 0.2


def _calculate_row_count_for_team(team: Team):

    # todo: update row counts for all tables in team by fetching from bigquery

    team.row_count = team.num_rows

    if team.enabled and team.row_count > team.row_limit * (1 + WARNING_BUFFER):
        team.enabled = False
    elif not team.enabled and team.row_count <= team.row_limit:
        team.enabled = True

    team.save()

    # todo: disable connectors


@shared_task
def update_team_row_limits():

    for team in Team.objects.all():
        _calculate_row_count_for_team(team)
