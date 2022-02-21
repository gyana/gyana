from allauth.account.views import SignupView
from django.shortcuts import get_object_or_404, redirect
from django.urls.base import reverse
from django.views.generic import DetailView
from turbo_response.mixins import TurboFormMixin
from turbo_response.response import HttpResponseSeeOther
from turbo_response.views import TurboFormView

from apps.base.mixins import PageTitleMixin
from apps.base.views import TurboUpdateView
from apps.teams.mixins import TeamMixin
from apps.users.helpers import require_email_confirmation

from .forms import (
    AppsumoCodeForm,
    AppsumoRedeemForm,
    AppsumoRedeemNewTeamForm,
    AppsumoSignupForm,
)
from .models import AppsumoCode


class AppsumoLanding(TurboFormView):
    template_name = "appsumo/landing.html"
    form_class = AppsumoCodeForm

    def form_valid(self, form):
        return HttpResponseSeeOther(
            reverse("appsumo:redirect", args=(form.cleaned_data["code"],))
        )


class AppsumoRedirect(PageTitleMixin, DetailView):
    model = AppsumoCode
    template_name = "appsumo/already_redeemed.html"
    slug_url_kwarg = "code"
    slug_field = "code"
    page_title = "AppSumo"

    def get(self, request, *args, **kwargs):

        self.object = self.get_object()

        if self.object.redeemed is None:
            if self.request.user.is_authenticated:
                return redirect(reverse("appsumo:redeem", args=(self.object.code,)))
            return redirect(reverse("appsumo:signup", args=(self.object.code,)))

        return super().get(request, *args, **kwargs)


class AppsumoSignup(PageTitleMixin, TurboFormMixin, SignupView):
    template_name = "appsumo/signup.html"
    page_title = "AppSumo"

    @property
    def code(self):
        return AppsumoCode.objects.get(code=self.kwargs.get("code"))

    # need to override otherwise global settings are used
    def get_form_class(self):
        return AppsumoSignupForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["code"] = self.code
        return kwargs

    def get_success_url(self):
        if require_email_confirmation():
            return reverse("account_email_verification_sent")

        return reverse("users:onboarding")


class AppsumoRedeem(TurboUpdateView):
    model = AppsumoCode
    slug_url_kwarg = "code"
    slug_field = "code"
    template_name = "appsumo/redeem.html"

    @property
    def team_exists(self):
        return self.request.user.teams.count() > 0

    def get_form_class(self):
        return AppsumoRedeemForm if self.team_exists else AppsumoRedeemNewTeamForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse("web:home")


class AppsumoStack(TeamMixin, TurboFormView):
    template_name = "appsumo/stack.html"
    form_class = AppsumoCodeForm

    def form_valid(self, form):
        code = get_object_or_404(AppsumoCode, code=form.cleaned_data["code"])
        code.redeem_team(self.team, self.request.user)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("teams:account", args=(self.team.id,))


# Incentivised reviews are disabled due to new AppSumo policy

# class AppsumoReview(TeamMixin, TurboCreateView):
#     model = AppsumoReview
#     form_class = AppsumoReviewForm
#     template_name = "appsumo/review.html"

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["team"] = self.team
#         return kwargs

#     def get_success_url(self) -> str:
#         return reverse("teams:account", args=(self.team.id,))
