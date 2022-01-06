from django.db import models
from waffle.models import CACHE_EMPTY, AbstractUserFlag
from waffle.utils import get_cache, get_setting, keyfmt

# adapted from https://waffle.readthedocs.io/en/stable/types/flag.html#custom-flag-models

cache = get_cache()


class Flag(AbstractUserFlag):
    FLAG_COMPANIES_CACHE_KEY = "FLAG_COMPANIES_CACHE_KEY"
    FLAG_COMPANIES_CACHE_KEY_DEFAULT = "flag:%s:teams"

    teams = models.ManyToManyField("teams.Team", blank=True, related_name="flags")

    title = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    # font awesome class name
    icon = models.CharField(max_length=128)
    # is feature available for public beta
    is_public_beta = models.BooleanField(default=False)

    def get_flush_keys(self, flush_keys=None):
        flush_keys = super().get_flush_keys(flush_keys)
        companies_cache_key = get_setting(
            Flag.FLAG_COMPANIES_CACHE_KEY, Flag.FLAG_COMPANIES_CACHE_KEY_DEFAULT
        )
        flush_keys.append(keyfmt(companies_cache_key, self.name))
        return flush_keys

    def is_active_for_user(self, user):
        is_active = super().is_active_for_user(user)
        if is_active:
            return is_active

        flag_team_ids = self._get_team_ids()
        user_team_ids = user.teams.all().values_list("pk", flat=True)

        if user_team_ids & flag_team_ids:
            return True

    def _get_team_ids(self):
        cache_key = keyfmt(
            get_setting(
                Flag.FLAG_COMPANIES_CACHE_KEY,
                Flag.FLAG_COMPANIES_CACHE_KEY_DEFAULT,
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
