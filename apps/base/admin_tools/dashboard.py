"""
This file was generated with the customdashboard management command, it
contains the two classes for the main dashboard and app index dashboard.
You can customize these classes as you want.

To activate your index dashboard add the following to your settings.py::
    ADMIN_TOOLS_INDEX_DASHBOARD = 'gyana.dashboard.CustomIndexDashboard'

And to activate the app index dashboard::
    ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'gyana.dashboard.CustomAppIndexDashboard'
"""

from admin_tools.dashboard import Dashboard, modules
from admin_tools.utils import get_admin_site_name
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for gyana.
    """

    def init_with_context(self, context):
        site_name = get_admin_site_name(context)
        # append a link list module for "quick links"
        self.children.append(
            modules.LinkList(
                _("Quick links"),
                layout="inline",
                draggable=False,
                deletable=False,
                collapsible=False,
                children=[
                    [_("Return to site"), "/"],
                    [_("Go to CMS"), "/cms"],
                    [_("Change password"), reverse("%s:password_change" % site_name)],
                    [_("Log out"), reverse("%s:logout" % site_name)],
                ],
            )
        )

        self.children.append(
            modules.ModelList(
                _("Account management"),
                models=("apps.users.models.CustomUser", "apps.teams.models.Team"),
            )
        )

        self.children.append(
            modules.ModelList(
                _("Waitlist"),
                models=("apps.users.models.ApprovedWaitlistEmail*"),
            )
        )

        self.children.append(
            modules.ModelList(
                _("Feature flippers"),
                models=("waffle.*", "apps.teams.flag.Flag"),
            )
        )

        # append an app list module for "Administration"
        self.children.append(
            modules.ModelList(
                _("Administration"),
                models=("django.contrib.*", "allauth.*", "django_celery_beat.*"),
            )
        )

        # append a recent actions module
        self.children.append(modules.RecentActions(_("Recent Actions"), 5))
