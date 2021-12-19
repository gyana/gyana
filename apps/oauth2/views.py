from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from requests_oauthlib import OAuth2Session

from apps.base.turbo import TurboCreateView, TurboUpdateView

from .forms import OAuth2Form
from .models import OAuth2
from .tables import OAuth2Table


class OAuth2List(SingleTableView):
    template_name = "oauth2/list.html"
    model = OAuth2
    table_class = OAuth2Table
    paginate_by = 20


class OAuth2Create(TurboCreateView):
    template_name = "oauth2/create.html"
    model = OAuth2
    form_class = OAuth2Form
    success_url = reverse_lazy("oauth2:list")


class OAuth2Detail(DetailView):
    template_name = "oauth2/detail.html"
    model = OAuth2


class OAuth2Update(TurboUpdateView):
    template_name = "oauth2/update.html"
    model = OAuth2
    form_class = OAuth2Form
    success_url = reverse_lazy("oauth2:list")


class OAuth2Delete(DeleteView):
    template_name = "oauth2/delete.html"
    model = OAuth2
    success_url = reverse_lazy("oauth2:list")


class OAuth2Login(DetailView):
    model = OAuth2

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        session = OAuth2Session(self.object.client_id)
        authorization_url, state = session.authorization_url(
            self.object.authorization_base_url
        )

        # State is used to prevent CSRF, keep this for later
        self.object.state = state
        self.object.save()

        return redirect(authorization_url)


class OAuth2Callback(DetailView):
    model = OAuth2

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        github = OAuth2Session(self.object.client_id, state=self.object.state)
        self.object.token = github.fetch_token(
            self.object.token_url,
            client_secret=self.object.client_secret,
            authorization_response=request.build_absolute_uri(),
        )
        self.object.save()

        return redirect(
            "project_integrations:configure",
            self.object.integration.project.id,
            self.object.integration.id,
        )
