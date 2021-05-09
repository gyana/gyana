import json

import djstripe
import stripe
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from djstripe.enums import PlanInterval
from djstripe.models import Product
from djstripe import settings as djstripe_settings
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.utils.decorators import catch_stripe_errors
from apps.web.meta import absolute_url
from .decorators import redirect_subscription_errors
from .helpers import get_friendly_currency_amount
from .metadata import (
    get_active_products_with_metadata,
    get_product_and_metadata_for_subscription,
    ACTIVE_PLAN_INTERVALS,
    get_active_plan_interval_metadata,
)

from apps.teams.decorators import team_admin_required, login_and_team_required
from apps.teams.models import Team


class ProductWithMetadataAPI(APIView):
    def get(self, request, *args, **kw):
        products_with_metadata = get_active_products_with_metadata()
        return Response(data=[p.to_dict() for p in products_with_metadata])


@redirect_subscription_errors
@login_required
def subscription(request, subscription_holder=None):
    subscription_holder = subscription_holder if subscription_holder else request.user
    if subscription_holder.has_active_subscription():
        return _view_subscription(request, subscription_holder)
    else:
        return _upgrade_subscription(request, subscription_holder)


def _view_subscription(request, subscription_holder):
    """
    Show user's active subscription
    """
    assert subscription_holder.has_active_subscription()
    return render(
        request,
        "subscriptions/view_subscription.html",
        {
            "active_tab": "subscription",
            "subscription": subscription_holder.active_stripe_subscription,
            "subscription_urls": _get_subscription_urls(subscription_holder),
            "friendly_payment_amount": get_friendly_currency_amount(
                subscription_holder.active_stripe_subscription.plan.amount,
                subscription_holder.active_stripe_subscription.plan.currency,
            ),
            "product": get_product_and_metadata_for_subscription(
                subscription_holder.active_stripe_subscription
            ),
        },
    )


def _upgrade_subscription(request, subscription_holder):
    """
    Show subscription upgrade form / options.
    """
    assert not subscription_holder.has_active_subscription()

    active_products = list(get_active_products_with_metadata())
    default_products = [p for p in active_products if p.metadata.is_default]
    default_product = default_products[0] if default_products else active_products[0]

    def _to_dict(product_with_metadata):
        # for now, just serialize the minimum amount of data needed for the front-end
        product_data = {}
        if PlanInterval.year in ACTIVE_PLAN_INTERVALS:
            product_data["annual_plan"] = {
                "stripe_id": product_with_metadata.annual_plan.id,
                "payment_amount": get_friendly_currency_amount(
                    product_with_metadata.annual_plan.amount,
                    product_with_metadata.annual_plan.currency,
                ),
                "monthly_amount": get_friendly_currency_amount(
                    product_with_metadata.annual_plan.amount / 12,
                    product_with_metadata.annual_plan.currency,
                ),
                "interval": PlanInterval.year,  # set to month because we're dividing price by 12
            }
        if PlanInterval.month in ACTIVE_PLAN_INTERVALS:
            product_data["monthly_plan"] = {
                "stripe_id": product_with_metadata.monthly_plan.id,
                "payment_amount": get_friendly_currency_amount(
                    product_with_metadata.monthly_plan.amount,
                    product_with_metadata.monthly_plan.currency,
                ),
                "monthly_amount": get_friendly_currency_amount(
                    product_with_metadata.monthly_plan.amount,
                    product_with_metadata.monthly_plan.currency,
                ),
                "interval": PlanInterval.month,
            }
        return product_data

    return render(
        request,
        "subscriptions/upgrade_subscription.html",
        {
            "active_tab": "subscription",
            "stripe_api_key": djstripe_settings.STRIPE_PUBLIC_KEY,
            "default_product": default_product,
            "active_products": active_products,
            "active_products_json": {
                str(p.stripe_id): _to_dict(p) for p in active_products
            },
            "active_plan_intervals": get_active_plan_interval_metadata(),
            "default_to_annual": ACTIVE_PLAN_INTERVALS[0] == PlanInterval.year,
            "subscription_urls": _get_subscription_urls(subscription_holder),
            "payment_metadata": _get_payment_metadata_from_request(request),
        },
    )


def _get_payment_metadata_from_request(request):
    return {
        "user_id": request.user.id,
        "user_email": request.user.email,
        "team_id": request.team.id,
    }


@login_required
def subscription_success(request):
    return _subscription_success(request, request.user)


def _subscription_success(request, subscription_holder):
    stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY
    if not subscription_holder.has_active_subscription():
        subscription = subscription_holder.subscription
        if not subscription:
            messages.error(
                request,
                "Oops, it looks like there was a problem processing your payment. "
                "Please try again, or get in touch if you think this is a mistake.",
            )
        else:
            # 3D-Secure workflow hopefully completed successfully,
            # re-sync the subscription and hopefully it will be active
            subscription.sync_from_stripe_data(subscription.api_retrieve())

    if subscription_holder.has_active_subscription():
        subscription_name = get_product_and_metadata_for_subscription(
            subscription_holder.active_stripe_subscription
        ).metadata.name
        messages.success(
            request,
            f"You've successfully signed up for {subscription_name}. "
            "Thanks so much for the support!",
        )
        # notify admins when someone signs up
        mail_admins(
            subject=f"Hooray! Someone just signed up for a {subscription_name} subscription!",
            message="Email: {}".format(request.user.email),
            fail_silently=True,
        )

    assert isinstance(subscription_holder, Team)
    redirect = reverse(
        "subscriptions_team:subscription_details", args=[subscription_holder.slug]
    )

    return HttpResponseRedirect(redirect)


@login_required
@require_POST
def create_stripe_portal_session(request, subscription_holder=None):
    subscription_holder = subscription_holder if subscription_holder else request.user
    subscription_urls = _get_subscription_urls(subscription_holder)

    stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY
    if (
        not subscription_holder.subscription
        or not subscription_holder.subscription.customer
    ):
        messages.error(
            request,
            _("Whoops, we couldn't find a subscription associated with your account!"),
        )
        return HttpResponseRedirect(subscription_urls["subscription_details"])

    session = stripe.billing_portal.Session.create(
        customer=subscription_holder.subscription.customer.id,
        return_url=absolute_url(subscription_urls["subscription_details"]),
    )
    return HttpResponseRedirect(session.url)


@login_required
@require_POST
@catch_stripe_errors
@transaction.atomic
def create_customer(request, subscription_holder=None):
    """
    Create a Stripe Customer and Subscription object and map them onto the subscription_holder

    Expects the inbound POST data to look something like this:
    {
        'email': 'cory@example.com',
        'userId': '23',
        'payment_method': 'pm_1GGgZaIYTEadrA0y0tthZ5UH'
    }
    """
    subscription_holder = subscription_holder if subscription_holder else request.user
    request_body = json.loads(request.body.decode("utf-8"))
    user_id = int(request_body["user_id"])
    email = request_body["user_email"]
    assert request.user.id == user_id
    assert request.user.email == email

    assert isinstance(subscription_holder, Team)
    team_id = int(request_body["team_id"])
    assert request.team.id == team_id

    payment_method = request_body["payment_method"]
    plan_id = request_body["plan_id"]
    stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY

    # first sync payment method to local DB to workaround https://github.com/dj-stripe/dj-stripe/issues/1125
    payment_method_obj = stripe.PaymentMethod.retrieve(payment_method)
    djstripe.models.PaymentMethod.sync_from_stripe_data(payment_method_obj)

    # create customer objects
    # This creates a new Customer in stripe and attaches the default PaymentMethod in one API call.
    customer = stripe.Customer.create(
        payment_method=payment_method,
        email=email,
        invoice_settings={
            "default_payment_method": payment_method,
        },
    )

    # create the local customer object in the DB so the subscription can use it
    djstripe.models.Customer.sync_from_stripe_data(customer)

    # create subscription
    subscription = stripe.Subscription.create(
        customer=customer.id,
        items=[
            {
                "plan": plan_id,
            },
        ],
        expand=["latest_invoice.payment_intent", "pending_setup_intent"],
    )
    djstripe_subscription = djstripe.models.Subscription.sync_from_stripe_data(
        subscription
    )

    # set subscription object on the subscription holder
    subscription_holder.subscription = djstripe_subscription
    subscription_holder.save()

    data = {"customer": customer, "subscription": subscription}
    return JsonResponse(
        data=data,
    )


def _get_subscription_urls(subscription_holder):
    # get URLs for subscription helpers
    url_bases = [
        "subscription_details",
        "create_customer",
        "create_stripe_portal_session",
        "subscription_success",
        "subscription_demo",
        "subscription_gated_page",
    ]

    def _construct_url(base):
        return reverse(f"subscriptions_team:{base}", args=[subscription_holder.slug])

    return {url_base: _construct_url(url_base) for url_base in url_bases}


@login_required
def subscription_demo(request, subscription_holder=None):
    subscription_holder = subscription_holder if subscription_holder else request.user
    return render(
        request,
        "subscriptions/demo.html",
        {
            "active_tab": "subscription_demo",
            "subscription": subscription_holder.active_stripe_subscription,
            "product": get_product_and_metadata_for_subscription(
                subscription_holder.active_stripe_subscription
            ),
            "subscription_urls": _get_subscription_urls(subscription_holder),
        },
    )


@login_required
def subscription_gated_page(request, subscription_holder=None):
    subscription_holder = subscription_holder if subscription_holder else request.user
    if not subscription_holder.has_active_subscription():
        return render(request, "subscriptions/subscription_required.html")
    else:
        return render(request, "subscriptions/subscription_gated_page.html")


@team_admin_required
def team_subscription(request, team_slug):
    return subscription(request, subscription_holder=request.team)


@team_admin_required
def team_subscription_success(request, team_slug):
    return _subscription_success(request, subscription_holder=request.team)


@team_admin_required
@require_POST
def team_create_stripe_portal_session(request, team_slug):
    return create_stripe_portal_session(request, request.team)


@team_admin_required
@require_POST
@catch_stripe_errors
@transaction.atomic
def team_create_customer(request, team_slug):
    return create_customer(request, request.team)


@login_and_team_required
def team_subscription_demo(request, team_slug):
    return subscription_demo(request, request.team)


@login_and_team_required
def team_subscription_gated_page(request, team_slug):
    return subscription_gated_page(request, subscription_holder=request.team)
