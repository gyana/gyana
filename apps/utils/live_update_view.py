from django import forms
from django.db import transaction
from django.http.response import HttpResponse
from turbo_response.views import TurboUpdateView


class LiveUpdateView(TurboUpdateView):
    @property
    def formsets(self):
        return []

    def get_formset_kwargs(self, formset):
        return {}

    def get_initial(self):
        initial = super().get_initial()

        for key in self.request.GET:
            initial[key] = self.request.GET[key]

        return initial

    def get_latest_attr(self, attr):
        return (
            self.request.POST.get(attr)
            or self.request.GET.get(attr)
            or getattr(self.object, attr)
        )

    def get_formset_instance(self, formset):

        form_kwargs = self.get_formset_kwargs(formset)

        # POST request for form creation
        if self.request.POST:
            return formset(
                self.request.POST,
                instance=self.object,
                form_kwargs=form_kwargs,
            )
        # GET request in live form
        if f"{formset.get_default_prefix()}-TOTAL_FORMS" in self.request.GET:
            return formset(
                self.request.GET,
                instance=self.object,
                form_kwargs=form_kwargs,
            )
        # initial render
        return formset(
            instance=self.object,
            form_kwargs=form_kwargs,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        for formset in self.formsets:
            context[
                f"{formset.get_default_prefix()}_formset"
            ] = self.get_formset_instance(formset)

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
