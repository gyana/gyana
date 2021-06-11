from django.urls import path

from . import views

app_name = "filters"

urlpatterns = [path("autocomplete", views.autocomplete_options, name="autocomplete")]
