from django.views.generic import DetailView, ListView

from .models import Post


class PostList(ListView):
    template_name = 'blog/list.html'
    model = Post
    ordering = ["-date"]

class PostDetail(DetailView):
    template_name = 'blog/detail.html'
    model = Post