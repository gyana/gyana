from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from rest_framework.decorators import api_view


def home(request):
    if request.user.is_authenticated:
        if not request.user.onboarded:
            return redirect("users:onboarding")

        if request.user.teams.count():
            team = request.user.teams.first()
            return redirect("teams:detail", team.id)

        return HttpResponseRedirect(reverse("teams:create"))

    return redirect("/accounts/login")


@api_view(["POST"])
def toggle_sidebar(request):
    request.session["sidebar_collapsed"] = not request.session.get(
        "sidebar_collapsed", True
    )

    return HttpResponse(200)
