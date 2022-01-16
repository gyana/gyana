from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from rest_framework.decorators import api_view

from apps.teams.models import Team


class Home(TemplateView):
    template_name = "web/home.html"

    def get(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            if not request.user.onboarded:
                return redirect("users:onboarding")

            if request.user.teams.count():
                session_team_id = request.session.get("team_id")
                team_id = (
                    session_team_id
                    if session_team_id
                    and Team.objects.filter(pk=session_team_id).exists()
                    else request.user.teams.first().id
                )

                return redirect("teams:detail", team_id)

            return HttpResponseRedirect(reverse("teams:create"))

        if not settings.ENABLE_WEBSITE:
            return redirect("account_login")

        return super().get(request, *args, **kwargs)


@api_view(["POST"])
def toggle_sidebar(request):
    request.session["sidebar_collapsed"] = not request.session.get(
        "sidebar_collapsed", True
    )

    return HttpResponse(200)
