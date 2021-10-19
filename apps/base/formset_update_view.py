from functools import cache

from django import forms
from django.db import transaction
from django.http.response import HttpResponse

from apps.base.live_update_form import LiveUpdateForm
from apps.base.turbo import TurboUpdateView

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
    "values": "Additional values",
}


def _get_formset_label(formset):
    prefix = formset.get_default_prefix()
    return FORMSET_LABELS.get(prefix, prefix)


class FormsetUpdateView(TurboUpdateView):
    def get_formset_class(self):
        if form := self.get_form():
            return form.get_live_formsets()
        return []

    def get_formset_form_kwargs(self, formset):
        return {}

    def get_formset_kwargs(self, formset):
        return {}

    def get_formset(self, formset):
        forms_kwargs = self.get_formset_form_kwargs(formset)

        # provide a reference to parent instance in live update forms
        if issubclass(formset.form, LiveUpdateForm):
            forms_kwargs["parent_instance"] = self.get_form_kwargs()["instance"]

        formset = (
            # POST request for form creation
            formset(
                self.request.POST,
                instance=self.object,
                **self.get_formset_kwargs(formset),
                form_kwargs=forms_kwargs,
            )
            # form is only bound if formset is in previous render, otherwise load from database
            if self.request.POST
            and f"{formset.get_default_prefix()}-TOTAL_FORMS" in self.request.POST
            # initial render
            else formset(
                instance=self.object,
                **self.get_formset_kwargs(formset),
                form_kwargs=forms_kwargs,
            )
        )
        # When the post contains the wrong total forms number new forms aren't
        # created. This happens for example when changing the widget kind.
        if len(formset.forms) < formset.min_num:
            formset.forms.extend(
                formset._construct_form(i, **forms_kwargs)
                for i in range(len(formset.forms), formset.min_num)
            )

        return formset

    @cache
    def get_formsets(self):
        return {
            _get_formset_label(formset): self.get_formset(formset)
            for formset in self.get_formset_class()
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formsets"] = self.get_formsets()
        return context

    def post(self, request, *args: str, **kwargs) -> HttpResponse:
        # override BaseUpdateView/ProcessFormView to check validation on formsets
        self.object = self.get_object()

        form = self.get_form()
        if form.is_valid() and all(
            formset.is_valid() for formset in self.get_formsets().values()
        ):
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form: forms.Form) -> HttpResponse:
        with transaction.atomic():
            self.object = form.save()
            for formset in self.get_formsets().values():
                if formset.is_valid():
                    formset.instance = self.object
                    formset.save()

        return super().form_valid(form)
