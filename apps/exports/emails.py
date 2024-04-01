from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse


def send_export_email(export, user):

    context = {
        "user": user,
        "download_link": f'{settings.EXTERNAL_URL}{reverse("exports:download", args=(export.id,))}',
    }

    subject = render_to_string(
        "exports/email/export_ready_subject.txt", context
    ).strip()
    text_body = render_to_string("exports/email/export_ready_message.txt", context)
    html_body = render_to_string("exports/email/export_ready_message.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        from_email="Gyana Notifications <notifications@gyana.com>",
        to=[user.email],
        body=text_body,
    )
    message.attach_alternative(html_body, "text/html")
    message.send()
