from django.views.generic.base import TemplateView

from apps.nodes.frames import FUNCTIONS


class FunctionReference(TemplateView):
    template_name = "nodes/help/function_reference.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["functions"] = FUNCTIONS
        return context
