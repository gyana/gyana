from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views
from .access import login_and_admin_required, login_and_team_required

app_name = "teams"

checkout_urlpatterns = (
    [
        path(
            "success",
            login_and_admin_required(views.CheckoutSuccess.as_view()),
            name="success",
        )
    ],
    "team_checkouts",
)

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

urlpatterns = [
    path("new", login_required(views.TeamCreate.as_view()), name="create"),
    path(
        "<hashid:team_id>",
        login_and_team_required(views.TeamDetail.as_view()),
        name="detail",
    ),
    path(
        "<hashid:team_id>/plan",
        login_and_admin_required(views.TeamPlan.as_view()),
        name="plan",
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
]
