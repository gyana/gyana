from functools import cache

from django import forms
from django.db import transaction
from django.http.response import HttpResponse
from django.views.generic.edit import CreateView, UpdateView
from turbo_response.mixins import TurboFormMixin

from .forms import LiveUpdateForm


class TurboCreateView(TurboFormMixin, CreateView):
    ...


class TurboUpdateView(TurboFormMixin, UpdateView):
    ...


# temporary overrides for formset labels
FORMSET_LABELS = {
    "columns": "Group columns",
    "aggregations": "Aggregations",
    "sort_columns": "Sort columns",
    "edit_columns": "Edit columns",
    "add_columns": "Add columns",
    "rename_columns": "Rename columns",
    "formula_columns": "Formula columns",
    "filters": "Filters",
    "secondary_columns": "Select specific columns",
    "window_columns": "Window columns",
    "convert_columns": "Select columns to convert",
    "values": "Additional values",
    "charts": "Charts",
    "queryparams": "Query Params",
    "httpheaders": "HTTP Headers",
    "formdataentries": "Form Data",
    "formurlencodedentries": "Form Data",
}


def _get_formset_label(formset):
    prefix = formset.get_default_prefix()
    return FORMSET_LABELS.get(prefix, prefix)


class FormsetUpdateView(TurboUpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formsets"] = context["form"].get_formsets()
        return context

    def post(self, request, *args: str, **kwargs) -> HttpResponse:
        # override BaseUpdateView/ProcessFormView to check validation on formsets
        self.object = self.get_object()

        form = self.get_form()
        if form.is_valid() and all(
            formset.is_valid() for formset in form.get_formsets().values()
        ):
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form: forms.Form) -> HttpResponse:
        with transaction.atomic():
            response = super().form_valid(form)
            for formset in form.get_formsets().values():
                if formset.is_valid():
                    # formset.instance = self.object
                    formset.save()

        return response
