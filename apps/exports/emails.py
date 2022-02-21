from datetime import datetime as dt
from datetime import timedelta

from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string

from apps.base import clients


def send_export_email(file_path, user):
    blob = clients.get_bucket().blob(file_path)
    download_link = blob.generate_signed_url(
        version="v4", expiration=dt.now() + timedelta(days=7), scheme="https"
    )

    context = {
        "user": user,
        "download_link": download_link,
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
