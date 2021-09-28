from apps.teams.models import CreditTransaction, Team


def test_credit():
    team = Team.create()
    team.credittransaction_set.create(
        amount=20, transaction_type=CreditTransaction.TransactionType.DECREASE
    )
