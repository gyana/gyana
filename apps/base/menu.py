"""
This file was generated with the custommenu management command, it contains
the classes for the admin menu, you can customize this class as you want.

To activate your custom menu add the following to your settings.py::
    ADMIN_TOOLS_MENU = 'gyana.menu.CustomMenu'
"""

from admin_tools.menu import Menu, items
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class CustomMenu(Menu):
    """
    Custom Menu for gyana admin site.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.children += [
            items.MenuItem(_("Dashboard"), reverse("admin:index")),
            items.Bookmarks(),
            items.ModelList(
                _("Applications"),
                exclude=("django.contrib.*", "allauth.*", "apps.appsumo.*"),
            ),
            items.ModelList(_("Appsumo"), models=("apps.appsumo.*",)),
            items.ModelList(
                _("Administration"), models=("django.contrib.*", "allauth.*")
            ),
        ]

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """
        return super().init_with_context(context)
