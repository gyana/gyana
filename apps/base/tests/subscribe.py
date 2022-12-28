import json
from datetime import timedelta
from uuid import uuid4

from django.utils import timezone
from djpaddle.models import Checkout, Subscription


def upgrade_to_pro(logged_in_user, team, pro_plan):

    checkout = Checkout.objects.create(
        id=uuid4(),
        completed=True,
        passthrough=json.dumps({"user_id": logged_in_user.id, "team_id": team.id}),
    )
    return Subscription.objects.create(
        id=uuid4(),
        subscriber=team,
        cancel_url="https://cancel.url",
        checkout_id=checkout.id,
        currency="USD",
        email=logged_in_user.email,
        event_time=timezone.now(),
        marketing_consent=True,
        next_bill_date=timezone.now() + timedelta(weeks=4),
        passthrough=json.dumps({"user_id": logged_in_user.id, "team_id": team.id}),
        quantity=1,
        source="test.url",
        status=Subscription.STATUS_ACTIVE,
        plan=pro_plan,
        unit_price=99,
        update_url="https://update.url",
        created_at=timezone.now(),
        updated_at=timezone.now(),
    )
