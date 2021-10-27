import pytest
from apps.appsumo.models import AppsumoCode, AppsumoExtra, AppsumoReview
from apps.teams.account import calculate_credit_statement, get_row_limit
from apps.teams.models import CreditTransaction, Team

pytestmark = pytest.mark.django_db


def test_row_limit():
    team = Team.objects.create(name="Test team")
    assert get_row_limit(team) == 50_000

    team.override_row_limit = 10
    assert get_row_limit(team) == 10

    team.override_row_limit = None
    AppsumoCode.objects.create(code="12345678", team=team)
    assert get_row_limit(team) == 1_000_000

    AppsumoReview.objects.create(
        team=team,
        review_link="https://appsumo.com/products/marketplace-gyana/#r666666",
    )
    assert get_row_limit(team) == 2_000_000

    AppsumoExtra.objects.create(team=team, rows=100_000, reason="extra")
    assert get_row_limit(team) == 2_100_000


def test_current_credit_balance_new_team():
    team = Team.objects.create(name="Test team")
    assert team.current_credit_balance == 0
    assert team.creditstatement_set.first() is None
    assert team.credittransaction_set.first() is None

    team.credittransaction_set.create(
        transaction_type=CreditTransaction.TransactionType.INCREASE, amount=5
    )
    team.credittransaction_set.create(
        transaction_type=CreditTransaction.TransactionType.INCREASE, amount=10
    )

    assert team.current_credit_balance == 15

    team.credittransaction_set.create(
        transaction_type=CreditTransaction.TransactionType.DECREASE, amount=15
    )
    assert team.current_credit_balance == 0


def test_current_credit_balance_existing_team():
    team = Team.objects.create(name="Test team")

    team.creditstatement_set.create(balance=0, credits_used=100, credits_received=50)
    team.credittransaction_set.create(
        transaction_type=CreditTransaction.TransactionType.INCREASE, amount=100
    )

    assert team.current_credit_balance == 100

    team.credittransaction_set.create(
        transaction_type=CreditTransaction.TransactionType.DECREASE, amount=25
    )
    assert team.current_credit_balance == 75


def test_reset_credits():
    team = Team.objects.create(name="Test team")
    team.creditstatement_set.create(balance=100, credits_used=0, credits_received=50)
    team.credittransaction_set.create(
        transaction_type=CreditTransaction.TransactionType.INCREASE, amount=42
    )

    assert team.current_credit_balance == 42

    calculate_credit_statement()

    assert team.current_credit_balance == 0
    latest_statement = team.creditstatement_set.latest("created")
    assert latest_statement.credits_used == 42
    assert latest_statement.balance == 42
