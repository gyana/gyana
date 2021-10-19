from django.db import models

from .models import CreditTransaction, Team

DEFAULT_ROW_LIMIT = 50_000
DEFAULT_CREDIT_LIMIT = 100


def get_row_limit(team: Team):
    from apps.appsumo.account import get_deal

    if team.override_row_limit is not None:
        return team.override_row_limit

    rows = max(
        DEFAULT_ROW_LIMIT,
        get_deal(team.appsumocode_set.all())["rows"],
    )

    # extra 1M for writing a review
    if hasattr(team, "appsumoreview"):
        rows += 1_000_000

    rows += team.appsumoextra_set.aggregate(models.Sum("rows"))["rows__sum"] or 0

    return rows


def get_credits(team: Team):
    from apps.appsumo.account import get_deal

    return max(DEFAULT_CREDIT_LIMIT, get_deal(team.appsumocode_set.all())["credits"])


def calculate_credit_statement_and_reset_balance():
    """Creates the credit statements for all teams and resets the balance to
    the plans limit."""
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
        # Create new credit statement
        team.creditstatement_set.create(
            balance=balance,
            credits_used=credits_used,
            credits_received=credits_received,
        )
        # Reset credits by adding the missing amount from the plan limit
        team.credittransaction_set.create(
            amount=team.credits - balance,
            transaction_type=CreditTransaction.TransactionType.INCREASE,
        )


def calculate_credit_balance(team):
    """Calculates the current credit balance based on the latest statement"""

    # Get the latest statement
    last_statement = (
        team.creditstatement_set.latest("created")
        if team.creditstatement_set.first()
        else None
    )

    start_balance = last_statement.balance if last_statement else team.credits

    # Fetch all transaction since the last statement
    # this includes a transaction filling up the balance to the plans maximum
    transactions = (
        team.credittransaction_set.filter(created__gt=last_statement.created)
        if last_statement
        else team.credittransaction_set
    )

    # Calculate the current balance adding the received credits to the balance of the last
    # statement and subtracting the used credits
    return (
        start_balance
        + (
            transactions.filter(
                transaction_type=CreditTransaction.TransactionType.INCREASE,
            ).aggregate(models.Sum("amount"))["amount__sum"]
            or 0
        )
        - (
            transactions.filter(
                transaction_type=CreditTransaction.TransactionType.DECREASE,
            ).aggregate(models.Sum("amount"))["amount__sum"]
            or 0
        )
    )
