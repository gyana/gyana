from django.urls import path

from . import views

app_name = "filters"

# TODO: Control access
urlpatterns = [path("autocomplete", views.autocomplete_options, name="autocomplete")]
