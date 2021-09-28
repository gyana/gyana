from celery.app import shared_task
from django.db import models

from apps.base.tasks import honeybadger_check_in

from .models import CreditTransaction, Team


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
def calculate_credit_balance():
    for team in Team.objects.all():
        balance = team.current_credit_balance
        last_statement = (
            team.creditstatement_set.latest("created")
            if team.creditstatement_set.first()
            else None
        )

        transactions = (
            team.credittransaction_set.filter(created__lt=last_statement.created)
            if last_statement
            else team.credittransaction_set
        )
        credits_received = (
            transactions.filter(
                transaction_type=CreditTransaction.TransactionType.INCREASE,
            ).aggregate(models.Sum("amount"))["amount__sum"]
            or 0
        )
        credits_used = (
            transactions.filter(
                transaction_type=CreditTransaction.TransactionType.DECREASE,
            ).aggregate(models.Sum("amount"))["amount__sum"]
            or 0
        )

        team.creditstatement_set.create(
            balance=balance,
            credits_used=credits_used,
            credits_received=credits_received,
        )

        team.credittransaction_set.create(
            amount=team.credits - balance,
            transaction_type=CreditTransaction.TransactionType.INCREASE,
            # TODO: figue out a solution for user
            user_id=1,
        )
