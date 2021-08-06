from functools import cached_property

from django import forms
from django.db import transaction
from django.http.response import HttpResponse
from turbo_response.views import TurboUpdateView

# temporary overrides for formset labels
FORMSET_LABELS = {
    "columns": "Columns",
    "aggregations": "Aggregations",
    "sort_columns": "Sort columns",
    "edit_columns": "Edit columns",
    "add_columns": "Add columns",
    "rename_columns": "Rename columns",
    "formula_columns": "Formula columns",
    "filters": "Filters",
    "secondary_columns": "Select specific columns",
    "window_columns": "Window columns",
    "values": "Additional values",
}


def _get_formset_label(formset):
    prefix = formset.get_default_prefix()
    return FORMSET_LABELS.get(prefix, prefix)


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
            # form is only bound if formset is in previous render, otherwise load from database
            if self.request.POST
            and f"{formset.get_default_prefix()}-TOTAL_FORMS" in self.request.POST
            # initial render
            else formset(instance=self.object, form_kwargs=forms_kwargs)
        )

        return formset_instance

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["formsets"] = {
            _get_formset_label(formset): self.get_formset_instance(formset)
            for formset in self.formsets
        }

        return context

    def form_valid(self, form: forms.Form) -> HttpResponse:
        context = self.get_context_data()

        if self.formsets:
            with transaction.atomic():
                self.object = form.save()
                for _, formset in context["formsets"].items():
                    if formset.is_valid():
                        formset.instance = self.object
                        formset.save()

        return super().form_valid(form)
