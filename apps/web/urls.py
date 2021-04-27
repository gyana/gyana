from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'web'
urlpatterns = [
    path('', views.home, name='home'),
    path('a/<slug:team_slug>', views.team_home, name='team_home'),
    path('a/<slug:team_slug>/manage/', views.team_admin_home, name='team_admin'),
    path('terms', TemplateView.as_view(template_name="web/terms.html"), name='terms'),
    path('404', TemplateView.as_view(template_name='404.html'), name='404'),
    path('500', TemplateView.as_view(template_name='500.html'), name='500'),
]
