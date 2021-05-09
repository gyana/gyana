from django.shortcuts import render

from .exceptions import SubscriptionConfigError


class redirect_subscription_errors(object):
    """
    Meant to be used with django views only.
    """
    def __init__(self, f):
        self.f = f

    def __call__(self, request, *args, **kwargs):
        try:
            return self.f(request, *args, **kwargs)
        except SubscriptionConfigError as e:
            return render(request, 'subscriptions/bad_config.html', {'error': str(e)}, status=500)
