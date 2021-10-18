from apps.teams.access import login_and_admin_required
from django.contrib.auth.decorators import login_required
from django.urls import path

from . import frames, views

app_name = "appsumo"
urlpatterns = [
    path("", views.AppsumoLanding.as_view(), name="landing"),
    path("signup/<slug:code>", views.AppsumoSignup.as_view(), name="signup"),
    path(
        "redeem/<slug:code>",
        login_required(views.AppsumoRedeem.as_view()),
        name="redeem",
    ),
    path("<slug:code>", views.AppsumoRedirect.as_view(), name="redirect"),
]

team_urlpatterns = (
    [
        path(
            "", login_and_admin_required(frames.AppsumoCodeList.as_view()), name="list"
        ),
        path(
            "stack",
            login_and_admin_required(views.AppsumoStack.as_view()),
            name="stack",
        ),
        path(
            "review",
            login_and_admin_required(views.AppsumoReview.as_view()),
            name="review",
        ),
        path(
            "extra",
            login_and_admin_required(frames.AppsumoExtra.as_view()),
            name="extra",
        ),
    ],
    "team_appsumo",
)
