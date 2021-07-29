from functools import cached_property

from django import forms
from django.db import transaction
from django.forms.utils import ErrorDict
from django.http.response import HttpResponse
from turbo_response.views import TurboUpdateView


class FormsetUpdateView(TurboUpdateView):
    @cached_property
    def formsets(self):
        return self.get_form().get_live_formsets()

    def get_formset_kwargs(self, formset):
        return {}

    def get_formset_instance(self, formset):

        forms_kwargs = {
            # provide a reference to parent instance in live update forms
            "parent_instance": self.get_form_kwargs()["instance"],
            **self.get_formset_kwargs(formset),
        }

        formset_instance = (
            # POST request for form creation
            formset(self.request.POST, instance=self.object, form_kwargs=forms_kwargs)
            if self.request.POST
            # initial render
            else formset(instance=self.object, form_kwargs=forms_kwargs)
        )

        # fix when formset.management_form was not defined in previous render
        # we can just ignore these errors
        formset_instance.management_form._errors = ErrorDict()

        return formset_instance

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["formsets"] = {
            formset.get_default_prefix(): self.get_formset_instance(formset)
            for formset in self.formsets
        }

        return context

    def form_valid(self, form: forms.Form) -> HttpResponse:
        context = self.get_context_data()

        if self.formsets:
            with transaction.atomic():
                self.object = form.save()
                for formset_cls in self.formsets:
                    formset = context[f"{formset_cls.get_default_prefix()}_formset"]
                    if formset.is_valid():
                        formset.instance = self.object
                        formset.save()

        return super().form_valid(form)
