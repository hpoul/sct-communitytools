from django.contrib.auth.models import User

from sphene.community import get_sph_setting
from sphene.community.middleware import get_current_group
from sphene.sphboard.models import UserPostCount


def is_spammer(user_id):
    apply_spammer_limits = False
    try:
        upc = UserPostCount.objects.get_post_count(User.objects.get(pk=user_id), get_current_group())
    except User.DoesNotExist:
        upc = 0
    if upc < get_sph_setting('board_signature_required_post_count'):
        apply_spammer_limits = True
    return apply_spammer_limits