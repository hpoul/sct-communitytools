from sphene.community import sphsettings
from sphene.community.sphutils import add_setting_defaults
from django.conf import settings


add_setting_defaults( {
    'board_count_views': True,
    'board_heat_days': 30,
    'board_heat_post_threshold': 10,
    'board_heat_view_threshold': 100,
    'board_heat_calculator': 'sphene.sphboard.models.calculate_heat',

    # Defines if the 'Notify Me' checkbox should be selected by default.
    'board_default_notifyme': True,

    # How long a user is allowed to edit his post in seconds.
    # -1: forever,
    # 0: never
    'board_edit_timeout': -1, #30 * 60,

    # How long a user is allowed to hide his post in seconds.
    # -1: forever,
    # 0: never
    'board_hide_timeout': -1, #30 * 60,

    # Timeout for the rendered body in the cache
    # Default 6 hours
    'board_body_cache_timeout': 6 * 3600,
    'board_signature_cache_timeout': 6 * 3600,
    'board_authorinfo_cache_timeout': 6 * 3600,

    # See http://code.djangoproject.com/ticket/4789
    # When activating this setting, select_related() will not be used.
    'workaround_select_related_bug': False,


    'board_post_paging': 10,

    # Allow users to attach files to their posts ?
    'board_allow_attachments': True,

    # Pass the board and blog posts through the wiki camel case
    # markup. This will allow wiki links to be automatically placed
    # into the posts. It is better to turn this off and use the
    # sph extended BBCODE wiki label.
    'board_auto_wiki_link_enabled': True,
    # default location of emoticons
    'board_emoticons_root': settings.STATIC_URL + 'sphene/emoticons/',
    'board_emoticons_list': {
            '0:-)': 'angel.gif',
            'O:-)':'angel.gif',
            ':angel:':'angel.gif',
            ':)':'smile.gif',
            ':(':'sad.gif',
            ':D':'grin.gif',
            ':p':'tongue.gif',
            ';)':'wink.gif',
            ':-)':'smile.gif',
            ':-(': 'sad.gif',
            ':-D': 'grin.gif',
            ':-P': 'tongue.gif',
            ':-p': 'tongue.gif',
            ':-/': 'unsure.gif',
            ':-\\': 'unsure.gif',
            ';-)': 'wink.gif',
            ':-$': 'confused.gif',
            ':-S': 'confused.gif',
            'B-)': 'cool.gif',
            ':lol:': 'lol.gif',
            ':batman:': 'batman.gif',
            ':rolleyes:': 'rolleyes.gif',
            ':icymad:': 'bluemad.gif',
            ':mad:': 'mad.gif',
            ':crying:': 'crying.gif',
            ':eek:': 'eek.gif',
            ':eyebrow:': 'eyebrow.gif',
            ':grim:': 'grim_reaper.gif',
            ':idea:': 'idea.gif',
            ':rotfl:': 'rotfl.gif',
            ':shifty:': 'shifty.gif',
            ':sleep:': 'sleep.gif',
            ':thinking:': 'thinking.gif',
            ':wave:': 'wave.gif',
            ':bow:': 'bow.gif',
            ':sheep:':  'sheep.gif',
            ':santa:':  'santaclaus.gif',
            ':anvil:': 'anvil.gif',
            ':bandit:': 'bandit.gif',
            ':chop:': 'behead.gif',
            ':biggun:': 'biggun.gif',
            ':mouthful:': 'blowingup,gif',
            ':gun:': 'bluekillsred.gif',
            ':box:': 'boxing.gif',
            ':gallows:': 'hanged.gif',
            ':jedi:': 'lightsaber1.gif',
            ':bosh:': 'mallet1.gif',
            ':saw:': 'saw.gif',
            ':stupid:': 'youarestupid.gif',
    },

    # default tag used when rendering user signatures in posts
    'board_signature_tag':'<div class="signature">%(signature)s</div>',

    # default link in board posts
    'board_post_link':'<a href="%(url)s">%(text)s</a>',

    'board_attachments_upload_to': 'var/sphene/sphwiki/attachment/%Y/%m/%d',

    'board_slugify_links': True,

    # Display the reply form directly below a thread instead of just a 'Post Reply' link.
    'board_quick_reply': False,

    # Activates the experimental WYSIWYG editor -
    #   only if 'bbcode' is the only markup choice.
    # If you are using it, please provide feedback in the
    # forums at http://sct.spene.net !
    'board_wysiwyg': False,
    # This options let users test the wysiwyg editor by appending
    # ?wysiwyg=1 to the post URL. (I just added it so it can be seen on
    # sct.sphene.net and tested by users.)
    'board_wysiwyg_testing': False,
    })


styleincludes = sphsettings.get_sph_setting( 'community_styleincludes', [])
styleincludes.append(settings.STATIC_URL + 'sphene/sphboard/styles/base.css')
sphsettings.set_sph_setting( 'community_styleincludes', styleincludes )
