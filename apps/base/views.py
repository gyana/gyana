from django.db import transaction
from django.utils.datastructures import MultiValueDict
from django.views.generic.edit import CreateView, UpdateView
from turbo_response.mixins import TurboFormMixin


class MultiValueDictMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if "data" in kwargs:
            kwargs["data"] = MultiValueDict({**kwargs["data"]})  # make it mutable
        return kwargs


class TurboCreateView(MultiValueDictMixin, TurboFormMixin, CreateView):
    ...


class TurboUpdateView(MultiValueDictMixin, TurboFormMixin, UpdateView):
    def post(self, request, *args: str, **kwargs):
        # override BaseUpdateView/ProcessFormView to check validation on formsets
        self.object = self.get_object()

        form = self.get_form()
        # stimulus controller POST request sets the "hidden_live" field
        if getattr(form, "is_live", False):
            # skip the turbo form mixin 422 status code
            return super(UpdateView, self).form_invalid(form)

        if form.is_valid() and all(
            formset.is_valid() for formset in form.get_formsets().values()
        ):
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            for formset in form.get_formsets().values():
                if formset.is_valid():
                    formset.save()

        return response
