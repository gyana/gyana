from django.views.generic import TemplateView


class HelpModal(TemplateView):
    template_name = "web/help.html"


class ChangelogModal(TemplateView):
    template_name = "web/changelog.html"