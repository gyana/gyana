from django.views.generic import DetailView, ListView

from .models import BlogIndexPage, BlogPage


class BlogList(ListView):
    template_name = 'blog/list.html'
    model = BlogPage
    ordering = ["-date"]

class BlogDetail(ListView):
    template_name = 'blog/detail.html'
    model = BlogPage