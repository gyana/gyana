from functools import wraps

from apps.dashboards.models import Dashboard
from apps.projects.access import login_and_project_required
from apps.teams.roles import user_can_access_team
from apps.widgets.models import Widget
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path
from django.urls.base import reverse
from rest_framework import routers

from . import views

app_name = "widgets"
urlpatterns = []

# drf config
router = routers.DefaultRouter()
router.register("api", views.WidgetPartialUpdate, basename="Widget")


def login_and_project_required_or_public(view_func):
    @wraps(view_func)
    def decorator(request, *args, **kwargs):
        widget = Widget.objects.get(pk=kwargs["pk"])
        if widget.dashboard.shared_status == Dashboard.SharedStatus.PUBLIC:
            return view_func(request, *args, **kwargs)
        user = request.user
        if not user.is_authenticated:
            return HttpResponseRedirect(
                "{}?next={}".format(reverse("account_login"), request.path)
            )
        team = widget.dashboard.project.team
        if user_can_access_team(user, team):
            return view_func(request, *args, **kwargs)

        return render(request, "404.html", status=404)

    return decorator


urlpatterns += router.urls

dashboard_urlpatterns = (
    [
        path("", login_and_project_required(views.WidgetList.as_view()), name="list"),
        path(
            "new",
            login_and_project_required(views.WidgetCreate.as_view()),
            name="create",
        ),
        path(
            "<hashid:pk>",
            login_and_project_required(views.WidgetDetail.as_view()),
            name="detail",
        ),
        path(
            "<hashid:pk>/update",
            login_and_project_required(views.WidgetUpdate.as_view()),
            name="update",
        ),
        path(
            "<hashid:pk>/delete",
            login_and_project_required(views.WidgetDelete.as_view()),
            name="delete",
        ),
        # No cache header tells browser to always re-validate the resource
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching#controlling_caching
        # https://web.dev/http-cache/#flowchart
        path(
            "<hashid:pk>/output",
            login_and_project_required_or_public(views.WidgetOutput.as_view()),
            name="output",
        ),
    ],
    "dashboard_widgets",
)
