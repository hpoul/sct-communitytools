from django.contrib.auth.models import User
from django.core.mail import get_connection, EmailMessage

from sphene.community.sphutils import get_sph_setting
from sphene.community.middleware import get_current_group


def is_spammer(user_id):
    from sphene.sphboard.models import UserPostCount
    user = User.objects.get(pk=user_id)
    if user.username in get_sph_setting('board_no_limits_users'):
        return False

    apply_spammer_limits = False
    try:
        upc = UserPostCount.objects.get_post_count(user, get_current_group())
    except User.DoesNotExist:
        upc = 0
    if upc < get_sph_setting('board_signature_required_post_count'):
        apply_spammer_limits = True
    return apply_spammer_limits


def send_mass_mail(datatuple, fail_silently=False, auth_user=None,
                   auth_password=None, connection=None):
    """
    Given a datatuple of (subject, message, from_email, recipient_list), sends
    each message to each recipient list. Returns the number of emails sent.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    If auth_user is None, the EMAIL_HOST_USER setting is used.
    If auth_password is None, the EMAIL_HOST_PASSWORD setting is used.

    Note: The API for this method is frozen. New code wanting to extend the
    functionality should use the EmailMessage class directly.
    """
    connection = connection or get_connection(username=auth_user,
                                              password=auth_password,
                                              fail_silently=fail_silently)
    messages = [EmailMessage(subject, message, sender, recipient, headers={'Precedence': 'bulk'})
                for subject, message, sender, recipient in datatuple]
    return connection.send_messages(messages)
