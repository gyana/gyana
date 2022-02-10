from django.views.generic import TemplateView
from wagtail.core.models import Page
from wagtail.search.models import Query

from .models import LearnPage


class Search(TemplateView):
    template_name = "learn/search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query", None)
        if query:
            results = LearnPage.objects.live().search(query)

            # Log the query so Wagtail can suggest promoted results
            Query.get(query).add_hit()
        else:
            results = LearnPage.objects.none()

        context["results"] = results
        context["learn_menu_page"] = LearnPage.objects.get(slug="learn")
        return context
