from django.urls import path

from . import views

app_name = "{{cookiecutter.app_name}}"
urlpatterns = [
    path("", views.{{ cookiecutter.model_name }}List.as_view(), name="list"),
    path("new", views.{{ cookiecutter.model_name }}Create.as_view(), name="create"),
    path("<hashid:pk>", views.{{ cookiecutter.model_name }}Detail.as_view(), name="detail"),
    path("<hashid:pk>/update", views.{{ cookiecutter.model_name }}Update.as_view(), name="update"),
    path("<hashid:pk>/delete", views.{{ cookiecutter.model_name }}Delete.as_view(), name="delete"),
]
