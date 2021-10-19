from celery.app import shared_task

from apps.base.tasks import honeybadger_check_in

from .account import calculate_credit_statement_and_reset_balance
from .models import Team


def _calculate_row_count_for_team(team: Team):

    # todo: update row counts for all tables in team by fetching from bigquery

    team.update_row_count()

    # todo: disable connectors


@shared_task
def update_team_row_limits():

    for team in Team.objects.all():
        _calculate_row_count_for_team(team)

    honeybadger_check_in("wqIPo7")


@shared_task
def calculate_monthly_credit_statement():
    calculate_credit_statement_and_reset_balance()
