from functools import cached_property

from .models import Team


class TeamMixin:
    @cached_property
    def team(self):
        return Team.objects.get(slug=self.kwargs["team_slug"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = self.team
        return context
