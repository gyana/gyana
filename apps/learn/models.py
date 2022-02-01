from wagtail.admin.edit_handlers import MultiFieldPanel, StreamFieldPanel
from wagtail.core import blocks
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.images.blocks import ImageChooserBlock
from wagtail.search import index

from apps.base.templatetags.help_utils import get_loom_embed_url

RICH_TEXT_FEATURES = (
    ["h2", "h3", "h4", "bold", "italic", "ol", "ul"]
    + ["hr", "link", "document-link", "image", "embed", "code"]
    + ["superscript", "subscript", "strikethrough", "blockquote"]
)


class LoomBlock(blocks.StructBlock):
    loom_id = blocks.CharBlock()
    caption = blocks.CharBlock(required=False)

    class Meta:
        template = "components/embed_loom.html"
        icon = "media"

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["loom_url"] = get_loom_embed_url(value["loom_id"])
        return context


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    caption = blocks.CharBlock(required=False)

    class Meta:
        template = "learn/blocks/image.html"
        icon = "image"


class LearnPage(Page):
    search_fields = Page.search_fields + [index.SearchField("body")]

    body = StreamField(
        [
            ("text", blocks.RichTextBlock(features=RICH_TEXT_FEATURES)),
            ("image", ImageBlock()),
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
