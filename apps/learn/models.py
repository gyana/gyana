import readtime
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page
from wagtail.search import index


class LearnPage(Page):
    body = RichTextField()
    search_fields = Page.search_fields + [index.SearchField("body")]

    content_panels = Page.content_panels + [
        FieldPanel("body", classname="full"),
    ]

    promote_panels = [MultiFieldPanel(Page.promote_panels, "Common page configuration")]

    parent_page_types = ["wagtailcore.Page", "learn.LearnPage"]
    subpage_types = ["learn.LearnPage"]

    @property
    def readtime(self):
        return readtime.of_html(self.body).text

    def get_context(self, request):
        context = super().get_context(request)
        context["learn_menu_page"] = Page.objects.get(slug="learn")
        return context
