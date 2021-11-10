from djpaddle.models import paddle_client


def get_subscriber_by_payload(team_model, payload):
    team_id = payload["team_id"]
    team = team_model.objects.filter(pk=team_id).first()

    if team is not None:
        return team


def list_payments_for_team(team)
    return paddle_client.list_subscription_payments(
            team.active_subscription.id, is_paid=True
        )

def get_plan_price_for_team_currency(plan, currency):
    return paddle_client.get_plan(plan.id)["recurring_price"][
            currency
        ]

def update_plan_for_team(team, plan_id):
    paddle_client.update_subscription(
        team.active_subscription.id, plan_id=plan_id
    )
