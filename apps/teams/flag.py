from django.db import models
from waffle.models import CACHE_EMPTY, AbstractUserFlag
from waffle.utils import get_cache, get_setting, keyfmt

# adapted from https://waffle.readthedocs.io/en/stable/types/flag.html#custom-flag-models

cache = get_cache()


class Flag(AbstractUserFlag):
    FLAG_TEAMS_CACHE_KEY = "FLAG_TEAMS_CACHE_KEY"
    FLAG_TEAMS_CACHE_KEY_DEFAULT = "flag:%s:teams"

    teams = models.ManyToManyField("teams.Team", blank=True, related_name="flags")

    @staticmethod
    def get_beta_flag():
        return Flag.objects.filter(name="beta").first()

    @staticmethod
    def check_team_in_beta(team):
        beta_flag = Flag.get_beta_flag()
        if beta_flag:
            return beta_flag.teams.filter(id=team.id).exists()

    @staticmethod
    def set_beta_program_for_team(team, beta_program):
        beta_flag = Flag.get_beta_flag()
        if beta_flag:
            already_in = Flag.check_team_in_beta(team)

            if beta_program != already_in:
                if beta_program:
                    beta_flag.teams.add(team)
                else:
                    beta_flag.teams.remove(team)
                # flush waffle cache so updates appear immediately
                beta_flag.flush()

    def get_flush_keys(self, flush_keys=None):
        flush_keys = super().get_flush_keys(flush_keys)
        teams_cache_key = get_setting(
            Flag.FLAG_TEAMS_CACHE_KEY, Flag.FLAG_TEAMS_CACHE_KEY_DEFAULT
        )
        flush_keys.append(keyfmt(teams_cache_key, self.name))
        return flush_keys

    def is_active_for_user(self, user):
        is_active = super().is_active_for_user(user)

        if is_active:
            return is_active

        flag_team_ids = self._get_team_ids()
        user_team_ids = set(user.teams.all().values_list("pk", flat=True))

        if user_team_ids & flag_team_ids:
            return True

    def _get_team_ids(self):
        cache_key = keyfmt(
            get_setting(
                Flag.FLAG_TEAMS_CACHE_KEY,
                Flag.FLAG_TEAMS_CACHE_KEY_DEFAULT,
            ),
            self.name,
        )
        cached = cache.get(cache_key)
        if cached == CACHE_EMPTY:
            return set()
        if cached:
            return cached

        team_ids = set(self.teams.all().values_list("pk", flat=True))
        if not team_ids:
            cache.add(cache_key, CACHE_EMPTY)
            return set()

        cache.add(cache_key, team_ids)
        return team_ids
