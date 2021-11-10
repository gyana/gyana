import paddle
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView, DetailView
from django.views.generic.edit import UpdateView
from django_tables2.views import SingleTableMixin, SingleTableView
from djpaddle.models import Checkout, Plan, paddle_client

from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.teams.mixins import TeamMixin

from .forms import MembershipUpdateForm, TeamCreateForm, TeamUpdateForm
from .models import Membership, Team
from .tables import TeamMembershipTable, TeamProjectsTable


class TeamCreate(TurboCreateView):
    model = Team
    form_class = TeamCreateForm
    template_name = "teams/create.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse("teams:plan", args=(self.object.id,))


class TeamPlan(TurboUpdateView):
    model = Team
    form_class = TeamCreateForm
    template_name = "teams/plan.html"
    pk_url_kwarg = "team_id"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["paddle_pro_plan"] = Plan.objects.get(pk=settings.DJPADDLE_PRO_PLAN_ID)
        context["paddle_business_plan"] = Plan.objects.get(
            pk=settings.DJPADDLE_BUSINESS_PLAN_ID
        )
        context["djpaddle_checkout_success_redirect"] = reverse(
            "team_checkouts:success", args=(self.object.id,)
        )
        context["DJPADDLE_VENDOR_ID"] = settings.DJPADDLE_VENDOR_ID
        context["DJPADDLE_SANDBOX"] = settings.DJPADDLE_SANDBOX
        return context

    def get_success_url(self) -> str:
        return reverse("teams:detail", args=(self.object.id,))


class TeamSubscription(TurboUpdateView):
    model = Team
    fields = []
    template_name = "teams/subscription.html"
    pk_url_kwarg = "team_id"

    # @property
    # def plan(self):
    #     return Plan.objects.get(pk=self.request.GET["plan_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["new_price"] = paddle_client.get_plan(self.plan.id)["recurring_price"][
        #     self.object.active_subscription.currency
        # ]
        # context["plan"] = self.plan
        return context

    def form_valid(self, form) -> HttpResponse:
        paddle_client.update_subscription(
            self.object.active_subscription.id, plan_id=self.plan.id
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("teams:account", args=(self.object.id,))


class TeamUpdate(TurboUpdateView):
    template_name = "teams/update.html"
    form_class = TeamUpdateForm
    model = Team
    pk_url_kwarg = "team_id"

    def get_success_url(self) -> str:
        return reverse("teams:update", args=(self.object.id,))


class TeamDelete(DeleteView):
    template_name = "teams/delete.html"
    model = Team
    pk_url_kwarg = "team_id"

    def get_success_url(self) -> str:
        return reverse("web:home")


class TeamDetail(SingleTableMixin, DetailView):
    template_name = "teams/detail.html"
    model = Team
    pk_url_kwarg = "team_id"
    table_class = TeamProjectsTable
    paginate_by = 15

    def get_context_data(self, **kwargs):
        from apps.projects.models import Project

        self.request.session["team_id"] = self.object.id
        self.projects = Project.objects.filter(team=self.object).filter(
            Q(access=Project.Access.EVERYONE) | Q(members=self.request.user)
        )

        context = super().get_context_data(**kwargs)
        context["project_count"] = self.projects.count()

        return context

    def get_table_data(self):
        return self.projects


class TeamAccount(UpdateView):
    template_name = "teams/account.html"
    model = Team
    pk_url_kwarg = "team_id"
    fields = []

    def form_valid(self, form) -> HttpResponse:
        self.object.update_row_count()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("teams:account", args=(self.object.id,))


class MembershipList(TeamMixin, SingleTableView):
    template_name = "members/list.html"
    model = Membership
    table_class = TeamMembershipTable
    paginate_by = 20

    def get_queryset(self):
        return Membership.objects.filter(team=self.team).all()


class MembershipUpdate(TeamMixin, TurboUpdateView):
    template_name = "members/update.html"
    model = Membership
    form_class = MembershipUpdateForm

    def get_success_url(self) -> str:
        return reverse("team_members:list", args=(self.team.id,))


class MembershipDelete(TeamMixin, DeleteView):
    template_name = "members/delete.html"
    model = Membership

    def delete(self, request, *args, **kwargs) -> HttpResponse:
        if self.get_object().can_delete:
            return super().delete(request, *args, **kwargs)
        raise Http404("Cannot delete last admin of team")

    def get_success_url(self) -> str:
        return reverse("team_members:list", args=(self.team.id,))


class CheckoutSuccess(TeamMixin, DetailView):
    template_name = "checkout/success.html"
    model = Checkout

    def get_object(self, queryset=None):
        return get_object_or_404(Checkout, id=self.request.GET.get("checkout"))
