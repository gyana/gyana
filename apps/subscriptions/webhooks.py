from django.core.mail import mail_admins
from djstripe import webhooks as djstripe_hooks
from djstripe.models import Customer, Subscription, Plan


@djstripe_hooks.handler("customer.subscription.updated")
def update_customer_plan(event, **kwargs):
    """
    This webhook is called when a customer updates their subscription via the Stripe
    billing portal.

    There are a few scenarios this can happen - if they are upgrading, downgrading
    cancelling (at the period end) or renewing after a cancellation.

    We update the subscription in place based on the possible fields, and
    these updates automatically trickle down to the user/team that holds the subscription.
    """
    # extract new plan and subscription ID
    new_plan = get_plan_data(event.data)
    subscription_id = get_subscription_id(event.data)

    # find associated subscription and change the plan details accordingly
    dj_subscription = Subscription.objects.get(id=subscription_id)
    dj_subscription.plan = Plan.objects.get(id=new_plan['id'])
    dj_subscription.cancel_at_period_end = get_cancel_at_period_end(event.data)
    dj_subscription.save()


@djstripe_hooks.handler('customer.subscription.deleted')
def email_admins_when_subscriptions_canceled(event, **kwargs):
    # example webhook handler to notify admins when a subscription is deleted/canceled
    try:
        customer_email = Customer.objects.get(id=event.data['object']['customer']).email
    except Customer.DoesNotExist:
        customer_email = 'unavailable'

    mail_admins(
        'Someone just canceled their subscription!',
        f'Their email was {customer_email}'
    )


def get_plan_data(stripe_event_data):
    return stripe_event_data['object']['items']['data'][0]['plan']


def get_previous_plan_data(stripe_event_data):
    return stripe_event_data['previous_attributes']['items']['data'][0]['plan']


def get_subscription_id(stripe_event_data):
    return stripe_event_data['object']['items']['data'][0]['subscription']


def get_cancel_at_period_end(stripe_event_data):
    return stripe_event_data['object']['cancel_at_period_end']
