

from sphene.community.sphutils import add_setting_defaults



add_setting_defaults( {
    'wiki_attachments_upload_to': 'var/sphene/sphwiki/attachment/%Y/%m/%d',

    # If False nonexistent links will only have the CSS classes
    # 'sph_wikilink' and 'sph_nonexistent'
    # If True: link will have a prefix 'create:'
    'wiki_links_nonexistent_prefix': False,

    # If this option is True only logged in users with edit rights
    # will see a link to nonexistent wiki snips.
    'wiki_links_nonexistent_show_only_privileged': True,

    # The default class for images which are included in the
    # wiki using an {img ...} macro.
    # This class is added to the <img> tag as well as to the <a> tag.
    'wiki_macros_default_image_class': None,
    })
