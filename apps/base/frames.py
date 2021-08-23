from apps.base.formset_update_view import FormsetUpdateView
from apps.base.turbo import TurboCreateView, TurboUpdateView
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from turbo_response.mixins import (
    TurboFrameTemplateResponseMixin as BaseTurboFrameTemplateResponseMixin,
)


class TurboFrameTemplateResponseMixin(BaseTurboFrameTemplateResponseMixin):
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


class TurboFrameFormsetUpdateView(TurboFrameTemplateResponseMixin, FormsetUpdateView):
    pass
