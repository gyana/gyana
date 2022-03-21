from django.contrib.auth.decorators import login_required
from django.urls import include, path

from . import views
from .access import login_and_admin_required, login_and_team_required

app_name = "teams"

membership_urlpatterns = (
    [
        path(
            "",
            login_and_admin_required(views.MembershipList.as_view()),
            name="list",
        ),
        path(
            "<hashid:pk>/update",
            login_and_admin_required(views.MembershipUpdate.as_view()),
            name="update",
        ),
        path(
            "<hashid:pk>/delete",
            login_and_admin_required(views.MembershipDelete.as_view()),
            name="delete",
        ),
    ],
    "team_members",
)

paddle_urlpatterns = (
    [
        # https://github.com/pennersr/django-allauth/issues/1109
        path(
            "post-checkout/",
            views.PaddlePostCheckoutApiView.as_view(),
            name="post_checkout_api",
        ),
        path("", include("djpaddle.urls")),
    ],
    "djpaddle",
)

urlpatterns = [
    path("new", login_required(views.TeamCreate.as_view()), name="create"),
    path(
        "<hashid:team_id>",
        login_and_team_required(views.TeamDetail.as_view()),
        name="detail",
    ),
    path(
        "<hashid:team_id>/plans",
        login_and_admin_required(views.TeamPlans.as_view()),
        name="plans",
    ),
    path(
        "<hashid:team_id>/checkout",
        login_and_admin_required(views.TeamCheckout.as_view()),
        name="checkout",
    ),
    path(
        "<hashid:team_id>/subscription",
        login_and_admin_required(views.TeamSubscription.as_view()),
        name="subscription",
    ),
    path(
        "<hashid:team_id>/payments",
        login_and_admin_required(views.TeamPayments.as_view()),
        name="payments",
    ),
    path(
        "<hashid:team_id>/update",
        login_and_admin_required(views.TeamUpdate.as_view()),
        name="update",
    ),
    path(
        "<hashid:team_id>/delete",
        login_and_admin_required(views.TeamDelete.as_view()),
        name="delete",
    ),
    path(
        "<hashid:team_id>/account",
        login_and_admin_required(views.TeamAccount.as_view()),
        name="account",
    ),
    path(
        "<hashid:team_id>/pricing",
        login_and_admin_required(views.TeamPricing.as_view()),
        name="pricing",
    ),
]
