import json

from apps.base import clients


def get_subscriber_by_payload(Subscriber, payload):
    team_id = json.loads(payload["passthrough"])["team_id"]
    # Subscriber is Team model
    team = Subscriber.objects.filter(pk=team_id).first()

    if team is not None:
        return team


def list_payments_for_team(team):
    return clients.paddle().list_subscription_payments(
        team.active_subscription.id, is_paid=True
    )


def get_plan_price_for_currency(plan, currency):
    return clients.paddle().get_plan(plan.id)["recurring_price"][currency]


def update_plan_for_team(team, plan_id):
    clients.paddle().update_subscription(team.active_subscription.id, plan_id=plan_id)
