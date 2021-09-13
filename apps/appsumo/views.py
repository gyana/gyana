from allauth.account.views import SignupView
from apps.base.frames import TurboFrameListView
from apps.base.mixins import PageTitleMixin
from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.teams.mixins import TeamMixin
from apps.users.helpers import require_email_confirmation
from django.shortcuts import redirect
from django.urls.base import reverse
from django.utils import timezone
from django.views.generic import DetailView
from django_tables2 import SingleTableView
from turbo_response.mixins import TurboFormMixin
from turbo_response.views import TurboFormView

from .forms import (
    AppsumoLandingform,
    AppsumoRedeemForm,
    AppsumoRedeemNewTeamForm,
    AppsumoReviewForm,
    AppsumoSignupForm,
    AppsumoStackForm,
)
from .models import AppsumoCode, AppsumoReview
from .tables import AppsumoCodeTable


class AppsumoCodeList(TeamMixin, SingleTableView, TurboFrameListView):
    template_name = "appsumo/list.html"
    model = AppsumoCode
    table_class = AppsumoCodeTable
    paginate_by = 20
    turbo_frame_dom_id = "team_appsumo:list"

    def get_queryset(self):
        return self.team.appsumocode_set.all()


class AppsumoStack(TeamMixin, TurboFormView):
    template_name = "appsumo/stack.html"
    model = AppsumoCode
    form_class = AppsumoStackForm

    def form_valid(self, form):

        instance = form.cleaned_data["code"]
        instance.team = self.team
        instance.redeemed = timezone.now()
        instance.redeemed_by = self.request.user
        instance.save()

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("team_appsumo:list", args=(self.team.id,))


class AppsumoLanding(TurboFormView):
    template_name = "appsumo/landing.html"
    form_class = AppsumoLandingform

    def form_valid(self, form):
        return redirect("appsumo:redirect", form.cleaned_data["code"])


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

    # need to override otherwise global settings are used
    def get_form_class(self):
        return AppsumoSignupForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["code"] = self.kwargs.get("code")
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
        return self.request.user.teams.count()

    def get_form_class(self):
        return AppsumoRedeemForm if self.team_exists > 0 else AppsumoRedeemNewTeamForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse("web:home")


class AppsumoReview(TeamMixin, TurboCreateView):
    model = AppsumoReview
    form_class = AppsumoReviewForm
    template_name = "appsumo/review.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["team"] = self.team
        return kwargs

    def get_success_url(self) -> str:
        return reverse("team_appsumo:list", args=(self.team.id,))
