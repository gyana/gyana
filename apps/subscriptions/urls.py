from django.urls import path

from . import views


app_name = "subscriptions"

urlpatterns = [
    path(
        "api/active-products/",
        views.ProductWithMetadataAPI.as_view(),
        name="products_api",
    ),
]

team_urlpatterns = (
    [
        path("", views.team_subscription, name="subscription_details"),
        path(
            "subscription_success/",
            views.team_subscription_success,
            name="subscription_success",
        ),
        path("demo/", views.team_subscription_demo, name="subscription_demo"),
        path(
            "subscription-gated-page/",
            views.team_subscription_gated_page,
            name="subscription_gated_page",
        ),
        path(
            "stripe-portal/",
            views.team_create_stripe_portal_session,
            name="create_stripe_portal_session",
        ),
        path(
            "api/create_customer/", views.team_create_customer, name="create_customer"
        ),
    ],
    "subscriptions_team",
)
