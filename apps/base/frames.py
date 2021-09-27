from django.conf import settings
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import DeleteView
from honeybadger import honeybadger
from turbo_response.mixins import (
    TurboFrameTemplateResponseMixin as BaseTurboFrameTemplateResponseMixin,
)

from apps.base.formset_update_view import FormsetUpdateView
from apps.base.turbo import TurboCreateView, TurboUpdateView


class TurboFrame500Mixin:
    def dispatch(self, request, *args, **kwargs):
        if settings.DEBUG:
            return super().dispatch(request, *args, **kwargs)
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as exc:
            honeybadger.notify(exc)
            return (
                self.get_turbo_frame()
                .template("components/frame_error.html", {})
                .response(self.request)
            )


class TurboFrameTemplateResponseMixin(
    BaseTurboFrameTemplateResponseMixin, TurboFrame500Mixin
):
    def render_to_response(self, context, **response_kwargs):
        return self.render_turbo_frame(context, **response_kwargs)


class TurboFrameCreateView(TurboFrameTemplateResponseMixin, TurboCreateView):
    pass


class TurboFrameDetailView(TurboFrameTemplateResponseMixin, DetailView):
    pass


class TurboFrameUpdateView(TurboFrameTemplateResponseMixin, TurboUpdateView):
    pass


class TurboFrameDeleteView(TurboFrameTemplateResponseMixin, DeleteView):
    pass


class TurboFrameListView(TurboFrameTemplateResponseMixin, ListView):
    pass


class TurboFrameTemplateView(TurboFrameTemplateResponseMixin, TemplateView):
    pass


class TurboFrameFormsetUpdateView(TurboFrameTemplateResponseMixin, FormsetUpdateView):
    pass
