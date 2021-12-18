from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from requests_oauthlib import OAuth2Session

from apps.base.turbo import TurboCreateView
from apps.projects.mixins import ProjectMixin

from .forms import CustomApiCreateForm
from .models import CustomApi


class CustomApiCreate(ProjectMixin, TurboCreateView):
    template_name = "customapis/create.html"
    model = CustomApi
    form_class = CustomApiCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        kwargs["created_by"] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:configure",
            args=(self.project.id, self.object.integration.id),
        )


class CustomAPIOAuth2Login(DetailView):
    model = CustomApi

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        session = OAuth2Session(self.object.oauth2_client_id)
        authorization_url, state = session.authorization_url(
            self.object.oauth2_authorization_base_url
        )

        # State is used to prevent CSRF, keep this for later
        self.object.oauth2_state = state
        self.object.save()

        return redirect(authorization_url)


class CustomAPIOAuth2Callback(DetailView):
    model = CustomApi

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        github = OAuth2Session(
            self.object.oauth2_client_id, state=self.object.oauth2_state
        )
        self.object.oauth2_token = github.fetch_token(
            self.object.oauth2_token_url,
            client_secret=self.object.oauth2_client_secret,
            authorization_response=request.build_absolute_uri(),
        )
        self.object.save()

        return redirect(
            "project_integrations:configure",
            self.object.integration.project.id,
            self.object.integration.id,
        )
