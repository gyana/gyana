from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_invitation(invitation):
    email_context = {
        'invitation': invitation,
    }
    send_mail(
        subject="You're invited to {}!".format(settings.PROJECT_METADATA['NAME']),
        message=render_to_string('teams/email/invitation.txt', context=email_context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitation.email],
        fail_silently=False,
        html_message=render_to_string('teams/email/invitation.html', context=email_context),
    )


def process_invitation(invitation, user):
    invitation.team.members.add(user, through_defaults={'role': invitation.role})
    invitation.is_accepted = True
    invitation.accepted_by = user
    invitation.save()


def get_invitation_id_from_request(request):
    return (
        # URL takes precedence over session/cookie
        request.GET.get('invitation_id')
        or request.session.get('invitation_id')
    )


def clear_invite_from_session(request):
    if 'invitation_id' in request.session:
        del request.session['invitation_id']
