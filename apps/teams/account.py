from django.db import models

from .models import CreditTransaction, Team

DEFAULT_ROW_LIMIT = 50_000
DEFAULT_CREDIT_LIMIT = 100


def get_row_limit(team: Team):
    from apps.appsumo.account import get_deal

    if team.override_row_limit is not None:
        return team.override_row_limit

    if team.has_subscription:
        return team.plan["rows"]

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

    if team.has_subscription:
        return team.plan["credits"]

    return max(DEFAULT_CREDIT_LIMIT, get_deal(team.appsumocode_set.all())["credits"])


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
