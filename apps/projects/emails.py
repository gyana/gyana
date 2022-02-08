from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import get_template, render_to_string


def send_duplicate_email(user, project):
    context = {
        "user": user,
        "project": project,
    }

    subject = render_to_string(
        "projects/email/duplicate_ready_subject.txt", context
    ).strip()
    text_body = render_to_string("projects/email/duplicate_ready_message.txt", context)
    html_body = render_to_string("projects/email/duplicate_ready_message.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        from_email="Gyana Notifications <notifications@gyana.com>",
        to=[user.email],
        body=text_body,
    )
    message.attach_alternative(html_body, "text/html")
    message.send()
