from django.db import models

from .models import CreditTransaction, Team

DEFAULT_ROW_LIMIT = 50_000
DEFAULT_CREDIT_LIMIT = 100


def get_row_limit(team: Team):

    if team.override_row_limit is not None:
        return team.override_row_limit

    # TODO: How does this need to look without Appsumo
    return team.plan["rows"] if team.has_subscription else DEFAULT_ROW_LIMIT


def get_credits(team: Team):

    if team.override_credit_limit is not None:
        return team.override_credit_limit

    return team.plan["credits"] if team.has_subscription else DEFAULT_CREDIT_LIMIT


def calculate_credit_statement():
    """Creates the credit statements for all teams."""
    for team in Team.objects.all():
        balance = team.current_credit_balance

        last_statement = (
            team.creditstatement_set.latest("created")
            if team.creditstatement_set.first()
            else None
        )

        transactions = (
            team.credittransaction_set.filter(created__gt=last_statement.created)
            if last_statement
            else team.credittransaction_set
        )
        credits_used = (
            transactions.filter(
                transaction_type=CreditTransaction.TransactionType.INCREASE,
            ).aggregate(models.Sum("amount"))["amount__sum"]
            or 0
        )
        credits_received = (
            transactions.filter(
                transaction_type=CreditTransaction.TransactionType.DECREASE,
            ).aggregate(models.Sum("amount"))["amount__sum"]
            or 0
        )
        # Create new credit statement
        team.creditstatement_set.create(
            balance=balance,
            credits_used=credits_used,
            credits_received=credits_received,
        )


def calculate_credit_balance(team):
    """Calculates the current credit balance based on the latest statement"""
    # Get the latest statement
    last_statement = (
        team.creditstatement_set.latest("created")
        if team.creditstatement_set.first()
        else None
    )

    # Fetch all transaction since the last statement
    transactions = (
        team.credittransaction_set.filter(created__gt=last_statement.created)
        if last_statement
        else team.credittransaction_set
    )

    # Calculate the current balance adding the used credits subtracting the added credits
    return (
        transactions.filter(
            transaction_type=CreditTransaction.TransactionType.INCREASE,
        ).aggregate(models.Sum("amount"))["amount__sum"]
        or 0
    ) - (
        transactions.filter(
            transaction_type=CreditTransaction.TransactionType.DECREASE,
        ).aggregate(models.Sum("amount"))["amount__sum"]
        or 0
    )
