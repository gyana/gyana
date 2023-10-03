import readtime
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=255)
    avatar = models.URLField()


class Post(models.Model):

    slug = models.SlugField(max_length=255)
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    title = models.TextField()
    body = models.TextField()
    feed_image = models.URLField()
    author = models.ForeignKey(
        "blog.Author",
        on_delete=models.PROTECT,
    )

    @property
    def readtime(self):
        return readtime.of_html(self.body).text
