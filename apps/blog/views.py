import markdown
from django.views.generic import DetailView, ListView

from .models import Post


class PostList(ListView):
    template_name = 'blog/list.html'
    model = Post
    ordering = ["-date"]

class PostDetail(DetailView):
    template_name = 'blog/detail.html'
    model = Post

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['markdown'] = markdown.markdown(self.object.body)
        return context_data