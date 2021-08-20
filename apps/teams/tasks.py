from apps.tables.models import Table
from celery.app import shared_task
from django.db import models, transaction
from django.utils import timezone

from .models import Team


def _calculate_row_count_for_team(team: Team):

    # todo: update row counts for all tables in team by fetching from bigquery

    team.update_row_count()

    # todo: disable connectors


@shared_task
def update_team_row_limits():

    for team in Team.objects.all():
        _calculate_row_count_for_team(team)
