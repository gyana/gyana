from allauth.account.views import SignupView
from apps.base.turbo import TurboCreateView, TurboUpdateView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.urls.base import reverse
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView

from .forms import AppsumoCodeForm, AppsumoRedeemForm, AppsumoSignupForm
from .models import AppsumoCode
from .tables import AppsumoCodeTable


class AppsumoCodeList(SingleTableView):
    template_name = "appsumo/list.html"
    model = AppsumoCode
    table_class = AppsumoCodeTable
    paginate_by = 20


class AppsumoCodeCreate(TurboCreateView):
    template_name = "appsumo/create.html"
    model = AppsumoCode
    form_class = AppsumoCodeForm
    success_url = reverse_lazy("appsumo:list")


class AppsumoCodeDetail(DetailView):
    template_name = "appsumo/detail.html"
    model = AppsumoCode


class AppsumoCodeUpdate(TurboUpdateView):
    template_name = "appsumo/update.html"
    model = AppsumoCode
    form_class = AppsumoCodeForm
    success_url = reverse_lazy("appsumo:list")


class AppsumoCodeDelete(DeleteView):
    template_name = "appsumo/delete.html"
    model = AppsumoCode
    success_url = reverse_lazy("appsumo:list")


class AppsumoRedirect(DetailView):

    model = AppsumoCode
    template_name = "appsumo/already_redeemed.html"
    slug_url_kwarg = "code"
    slug_field = "code"

    def get(self, request, *args, **kwargs):

        self.object = self.get_object()

        if self.object.redeemed is None:
            if self.request.user.is_authenticated:
                return redirect(reverse("appsumo:redeem", args=(self.object.code,)))
            return redirect(reverse("appsumo:signup", args=(self.object.code,)))

        return super().get(request, *args, **kwargs)


class AppsumoSignup(SignupView):

    template_name = "appsumo/signup.html"
    # need to override otherwise global settings are used
    def get_form_class(self):
        return AppsumoSignupForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["code"] = self.kwargs.get("code")
        return kwargs


class AppsumoRedeem(TurboUpdateView):
    model = AppsumoCode
    form_class = AppsumoRedeemForm
    slug_url_kwarg = "code"
    slug_field = "code"
    template_name = "appsumo/redeem.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse("teams:detail", args=(self.object.team.id,))
