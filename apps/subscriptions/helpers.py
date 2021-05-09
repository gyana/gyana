from django.utils.functional import cached_property
from djstripe.enums import SubscriptionStatus
from djstripe.models import Subscription
from djstripe.utils import CURRENCY_SIGILS


class SubscriptionModelMixin:
    """
    Helper class to be used with Stripe Subscriptions.

    Assumes that the associated subclass is a django model containing a
    subscription field that is a ForeignKey to a djstripe.Subscription object.
    """
    # subclass should override with appropriate foreign keys as needed
    subscription = None

    @cached_property
    def active_stripe_subscription(self):
        if self.subscription and self.subscription.status == SubscriptionStatus.active:
            return self.subscription
        return None

    def has_active_subscription(self):
        return self.active_stripe_subscription is not None


def get_friendly_currency_amount(amount, currency):
    # modified from djstripe's version to only include sigil or currency, but not both
    currency = currency.upper()
    sigil = CURRENCY_SIGILS.get(currency, "")
    if sigil:
        return "{sigil}{amount:.2f}".format(sigil=sigil, amount=amount)
    else:
        return "{amount:.2f} {currency}".format(amount=amount, currency=currency)
