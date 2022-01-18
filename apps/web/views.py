from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from rest_framework.decorators import api_view

from apps.teams.models import Team

pain_points = [
    {
        "name": "😱",
        "description": "Repeating the same workflows <strong>every week</strong>",
    },
    {
        "name": "😫",
        "description": "<strong>Manually</strong> downloading CSVs from all my web tools",
    },
    {
        "name": "😅",
        "description": "Struggling to get <strong>access</strong> to the company database",
    },
    {
        "name": "🤔",
        "description": "Impossible to get that <strong>one</strong> chart for your dashboard",
    },
    {
        "name": "🌊",
        "description": "<strong>Drowning</strong> in data but no idea what to do with it",
    },
    {
        "name": "💸",
        "description": "Can't justify the spend on <strong>expensive</strong> tools",
    },
    {
        "name": "⌛",
        "description": "Spending <strong>all afternoon</strong> making a small change in a script",
    },
    {
        "name": "📥",
        "description": "Overwhelmed with <strong>ad hoc</strong> data requests from the team",
    },
]

features = [
    {
        "'name'": "Automate your work",
        "description": "Turn manual processes in automated workflows. Schedule periodic updates and build-reusable templates.",
        "icon": "sparkles",
    },
    {
        "name": "Connect to the web",
        "description": "Build a single data store for your business apps, marketing tools, databases and custom APIs. Always up to date.",
        "icon": "database",
    },
    {
        "name": "Pay for what you use",
        "description": "Our transparent pricing model scales with data usage, not users. Because you shouldn't have to pay to collaborate.",
        "icon": "credit-card",
    },
    {
        "name": "Empower your team",
        "description": "Turn ad hoc requests into repeatable solutions you can hand off to your team. Decentralize your expertise.",
        "icon": "user-group",
    },
    {
        "name": "Scale beyond your computer",
        "description": "Gyana works in cloud, not your local machine. No need to worry about spreadsheet row limits or overheated laptops.",
        "icon": "cloud",
    },
    {
        "name": "Manage your clients",
        "description": "Assign separate clients to isolated workspaces. Share unique links to your reports with custom branding and your domain.",
        "icon": "view-grid",
    },
]

use_cases = [
    {
        "name": "Agencies",
        "description": "Build custom <strong>PPC, organic and social dashboards</strong> and manage all your clients in one place.",
    },
    {
        "name": "B2B SaaS",
        "description": "Monitor all your user actions into a single funnel and <strong>optimize your growth flywheel</strong>.",
    },
    {
        "name": "eCommerce",
        "description": "Map the online purchasing journey and <strong>understand acquisition, CAC and LTV</strong>.",
    },
    {
        "name": "Consulting",
        "description": "Turn your custom analysis workflows into <strong>repeatable solutions</strong> to accelerate your work.",
    },
]


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pain_points"] = pain_points
        context["features"] = features
        context["use_cases"] = use_cases
        return context


@api_view(["POST"])
def toggle_sidebar(request):
    request.session["sidebar_collapsed"] = not request.session.get(
        "sidebar_collapsed", True
    )

    return HttpResponse(200)
