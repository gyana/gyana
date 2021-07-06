from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


def home(request):
    if request.user.is_authenticated:
        if request.user.teams.count():
            team = request.user.teams.first()
            return HttpResponseRedirect(reverse("teams:detail", args=(team.id,)))

        return HttpResponseRedirect(reverse("teams:create"))

    return redirect("/accounts/login")
