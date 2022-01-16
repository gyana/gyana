"""
This file was generated with the customdashboard management command, it
contains the two classes for the main dashboard and app index dashboard.
You can customize these classes as you want.

To activate your index dashboard add the following to your settings.py::
    ADMIN_TOOLS_INDEX_DASHBOARD = 'gyana.dashboard.CustomIndexDashboard'

And to activate the app index dashboard::
    ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'gyana.dashboard.CustomAppIndexDashboard'
"""

from admin_tools.dashboard import AppIndexDashboard, Dashboard, modules
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
                    [_("Change password"), reverse("%s:password_change" % site_name)],
                    [_("Log out"), reverse("%s:logout" % site_name)],
                ],
            )
        )

        # append an app list module for "Applications"
        self.children.append(
            modules.ModelList(
                _("Applications"),
                exclude=("django.contrib.*", "allauth.*", "apps.appsumo.*"),
            )
        )

        # appsumo
        self.children.append(
            modules.ModelList(
                _("Appsumo"),
                models=("apps.appsumo.*",),
            )
        )

        # append an app list module for "Administration"
        self.children.append(
            modules.ModelList(
                _("Administration"),
                models=("django.contrib.*", "allauth.*"),
            )
        )

        # append a recent actions module
        self.children.append(modules.RecentActions(_("Recent Actions"), 5))

        # # append a feed module
        # self.children.append(
        #     modules.Feed(
        #         _("Latest Django News"),
        #         feed_url="http://www.djangoproject.com/rss/weblog/",
        #         limit=5,
        #     )
        # )

        # # append another link list module for "support".
        # self.children.append(
        #     modules.LinkList(
        #         _("Support"),
        #         children=[
        #             {
        #                 "title": _("Django documentation"),
        #                 "url": "http://docs.djangoproject.com/",
        #                 "external": True,
        #             },
        #             {
        #                 "title": _('Django "django-users" mailing list'),
        #                 "url": "http://groups.google.com/group/django-users",
        #                 "external": True,
        #             },
        #             {
        #                 "title": _("Django irc channel"),
        #                 "url": "irc://irc.freenode.net/django",
        #                 "external": True,
        #             },
        #         ],
        #     )
        # )
