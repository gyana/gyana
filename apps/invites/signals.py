from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from .invitations import get_invitation_id_from_request, process_invitation
from .models import Invite


@receiver(user_signed_up)
def add_user_to_team(request, user, **kwargs):
    """
    Adds the user to the team if there is invitation information in the URL.
    """
    invitation_id = get_invitation_id_from_request(request)
    if invitation_id:
        try:
            invitation = Invite.objects.get(id=invitation_id)
            process_invitation(invitation, user)
        except Invite.DoesNotExist:
            # for now just swallow missing invitation errors
            # these should get picked up by the form validation
            pass
