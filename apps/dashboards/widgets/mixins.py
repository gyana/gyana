from functools import cached_property

from .models import Widget


class WidgetMixin:
    @cached_property
    def widget(self):
        return Widget.objects.get(pk=self.kwargs["widget_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["widget"] = self.widget
        return context
