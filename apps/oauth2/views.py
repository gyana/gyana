from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView
from requests_oauthlib import OAuth2Session

from apps.base.views import TurboCreateView, TurboUpdateView
from apps.projects.mixins import ProjectMixin

from .forms import OAuth2CreateForm, OAuth2UpdateForm
from .models import OAuth2


class OAuth2Create(ProjectMixin, TurboCreateView):
    template_name = "oauth2/create.html"
    model = OAuth2
    form_class = OAuth2CreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        return kwargs

    def get_success_url(self) -> str:
        return reverse("project_oauth2:update", args=(self.project.id, self.object.id))


class OAuth2Update(ProjectMixin, TurboUpdateView):
    template_name = "oauth2/update.html"
    model = OAuth2
    form_class = OAuth2UpdateForm

    def get_success_url(self) -> str:
        return reverse("oauth2:login", args=(self.object.id,))


class OAuth2Delete(ProjectMixin, DeleteView):
    template_name = "oauth2/delete.html"
    model = OAuth2

    def get_success_url(self) -> str:
        return reverse("projects:update", args=(self.project.id,))


class OAuth2Login(DetailView):
    model = OAuth2

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        session = OAuth2Session(self.object.client_id, scope=self.object.scope)
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

        return redirect("projects:update", self.object.project.id)
