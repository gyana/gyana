from django.contrib.auth.decorators import login_required
from django.urls import path

from . import rest

app_name = "filters"

# TODO: Control access
urlpatterns = [
    # rest
    path("autocomplete", login_required(rest.autocomplete_options), name="autocomplete")
]
