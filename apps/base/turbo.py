from django.views.generic.edit import CreateView, UpdateView
from turbo_response.mixins import TurboFormMixin


class TurboCreateView(TurboFormMixin, CreateView):
    ...


class TurboUpdateView(TurboFormMixin, UpdateView):
    ...
