import readtime
from django.db import models
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet


@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(max_length=255)

    panels = [FieldPanel("name")]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "blog categories"


@register_snippet
class BlogAuthor(models.Model):
    name = models.CharField(max_length=255)
    avatar = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("name"),
        ImageChooserPanel("avatar"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "blog authors"


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro", classname="full")]

    parent_page_types = ["wagtailcore.Page"]
    subpage_types = ["blog.BlogPage"]

    def get_context(self, request):
        context = super().get_context(request)
        blogpages = self.get_children().live().order_by("-first_published_at")
        context["blogpages"] = blogpages
        return context


class BlogPage(Page):

    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = RichTextField()
    feed_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    category = models.ForeignKey(
        "blog.BlogCategory",
        on_delete=models.PROTECT,
    )
    author = models.ForeignKey(
        "blog.BlogAuthor",
        on_delete=models.PROTECT,
    )

    search_fields = Page.search_fields + [
        index.SearchField("body"),
        index.FilterField("date"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("date"),
                FieldPanel("category"),
                FieldPanel("author"),
            ],
            heading="Blog information",
        ),
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        ImageChooserPanel("feed_image"),
    ]

    parent_page_types = ["blog.BlogIndexPage"]
    subpage_types = []

    @property
    def readtime(self):
        return readtime.of_html(self.body).text
