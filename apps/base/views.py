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
        if form.is_valid() and all(
            formset.is_valid() for formset in form.get_formsets().values()
        ):
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        # - when the Stimulus controller makes a POST request, it will be invalid
        # and re-render the same form with the updated values
        # - when the form is valid and the user clicks a submit button, it behaves
        # like a normal form
        if form.is_live:
            return self.form_invalid(form)

        with transaction.atomic():
            response = super().form_valid(form)
            for formset in form.get_formsets().values():
                if formset.is_valid():
                    formset.save()

        return response
