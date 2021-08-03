from django.urls import path

from . import rest

app_name = "filters"

# TODO: Control access
urlpatterns = [
    # rest
    path("autocomplete", rest.autocomplete_options, name="autocomplete")
]
