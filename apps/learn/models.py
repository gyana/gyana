from wagtail.admin.edit_handlers import MultiFieldPanel, StreamFieldPanel
from wagtail.core import blocks
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.images.blocks import ImageChooserBlock
from wagtail.search import index


class LoomBlock(blocks.URLBlock):
    class Meta:
        template = "components/embed_loom.html"
        icon = "video"

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["loom_url"] = value
        return context


class LearnPage(Page):
    search_fields = Page.search_fields + [index.SearchField("body")]

    body = StreamField(
        [
            ("heading", blocks.CharBlock(form_classname="full title")),
            ("paragraph", blocks.RichTextBlock()),
            ("image", ImageChooserBlock()),
            ("loom", LoomBlock()),
        ]
    )

    content_panels = Page.content_panels + [
        StreamFieldPanel("body"),
    ]

    promote_panels = [MultiFieldPanel(Page.promote_panels, "Common page configuration")]

    parent_page_types = ["wagtailcore.Page", "learn.LearnPage"]
    subpage_types = ["learn.LearnPage"]

    def get_context(self, request):
        context = super().get_context(request)
        context["learn_menu_page"] = Page.objects.get(slug="learn")
        return context
