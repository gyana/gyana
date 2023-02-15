import http

from django.db import transaction
from django.http import HttpResponseRedirect
from django.utils.datastructures import MultiValueDict
from django.views.generic.edit import CreateView as BaseCreateView
from django.views.generic.edit import UpdateView as BaseUpdateView


class LiveMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # When a node has no parents or parents break the form can't be constructed

        if context.get("form"):
            context["formsets"] = context["form"].get_formsets()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if "data" in kwargs:
            kwargs["data"] = MultiValueDict({**kwargs["data"]})  # make it mutable
        return kwargs

    def post(self, request, *args: str, **kwargs):
        # override BaseCreateView/BaseUpdateView and ProcessFormView for live
        # form logic and formset validation

        form = self.get_form()
        # stimulus controller POST request sets the "hidden_live" field
        if getattr(form, "is_live", False):
            # c.f. FormMixin.form_invalid
            return self.render_to_response(self.get_context_data(form=form))

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


class CreateView(LiveMixin, FormMixin, BaseCreateView):
    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)


class UpdateView(LiveMixin, FormMixin, BaseUpdateView):
    @property
    def is_preview_request(self):
        return self.request.POST.get("submit") == "Save & Preview"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)
