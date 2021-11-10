from datetime import datetime as dt
from datetime import timedelta

from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import get_template

from apps.base import clients


def send_export_email(file_path, user):
    blob = clients.get_bucket().blob(file_path)
    url = blob.generate_signed_url(
        version="v4", expiration=dt.now() + timedelta(days=7)
    )

    message_template_plain = get_template("exports/email/export_ready_message.txt")
    message_template = get_template("exports/email/export_ready_message.html")

    message = EmailMultiAlternatives(
        "Your export is ready",
        message_template_plain.render({"user": user, "url": url}),
        "Gyana Notifications <notifications@gyana.com>",
        [user.email],
    )
    message.attach_alternative(
        message_template.render({"user": user, "url": url}), "text/html"
    )
    message.send()
