from django.template.loader import render_to_string

from apps.base.alpine import ibis_store


def playwright_form(page, form):
    html = render_to_string("test/form.html", {"form": form, "ibis_store": ibis_store})
    page.set_content(html)
