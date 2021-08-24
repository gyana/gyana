from apps.teams.access import login_and_admin_required
from django.urls import path

from . import views

app_name = "appsumo"
urlpatterns = [
    path("signup/<slug:code>", views.AppsumoSignup.as_view(), name="signup"),
    path("redeem/<slug:code>", views.AppsumoRedeem.as_view(), name="redeem"),
    path("<slug:code>", views.AppsumoRedirect.as_view(), name="redirect"),
    # path("", views.AppsumoCodeList.as_view(), name="list"),
    # path("new", views.AppsumoCodeCreate.as_view(), name="create"),
    # path("<hashid:pk>", views.AppsumoCodeDetail.as_view(), name="detail"),
    # path("<hashid:pk>/update", views.AppsumoCodeUpdate.as_view(), name="update"),
    # path("<hashid:pk>/delete", views.AppsumoCodeDelete.as_view(), name="delete"),
]

team_urlpatterns = (
    [
        path(
            "", login_and_admin_required(views.AppsumoCodeList.as_view()), name="list"
        ),
    ],
    "team_appsumo",
)
