import http

from django.db import transaction
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView as BaseCreateView
from django.views.generic.edit import UpdateView as BaseUpdateView


class HttpResponseSeeOther(HttpResponseRedirect):
    """Redirect with 303 status"""

    status_code = http.HTTPStatus.SEE_OTHER


class FormMixin:
    """Mixin for handling form validation. Ensures response
    has 422 status on invalid and 303 on success"""

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(form=form),
            status=http.HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    def form_valid(self, form):
        super().form_valid(form)  # type: ignore
        return HttpResponseSeeOther(self.get_success_url())


class AlpineFormsetMixin:
    def post(self, request, *args: str, **kwargs):
        # override BaseCreateView/BaseUpdateView and ProcessFormView for alpine
        # form logic and formset validation

        form = self.get_form()
        self.formsets = form.get_formsets() if hasattr(form, "get_formsets") else []

        if form.is_valid() and all(formset.is_valid() for formset in self.formsets):
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            for formset in self.formsets:
                formset.save()

        return response


class CreateView(AlpineFormsetMixin, FormMixin, BaseCreateView):
    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)


class UpdateView(AlpineFormsetMixin, FormMixin, BaseUpdateView):
    @property
    def is_preview_request(self):
        return self.request.POST.get("submit") == "Save & Preview"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)
