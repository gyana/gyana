class PageTitleMixin(object):
    def get_page_title(self, context):
        return getattr(self, "page_title", None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.get_page_title(context)

        return context
