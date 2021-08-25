from apps.teams.access import login_and_admin_required
from django.urls import path

from . import views

app_name = "appsumo"
urlpatterns = [
    path("signup/<slug:code>", views.AppsumoSignup.as_view(), name="signup"),
    path("redeem/<slug:code>", views.AppsumoRedeem.as_view(), name="redeem"),
    path("<slug:code>", views.AppsumoRedirect.as_view(), name="redirect"),
]

team_urlpatterns = (
    [
        path(
            "", login_and_admin_required(views.AppsumoCodeList.as_view()), name="list"
        ),
        path("stack", views.AppsumoStack.as_view(), name="stack"),
        path("review", views.AppsumoReview.as_view(), name="review"),
    ],
    "team_appsumo",
)
