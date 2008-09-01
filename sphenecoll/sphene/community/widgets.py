from django import forms
from django.conf import settings

from sphene.community.sphutils import sph_reverse
from sphene.community.models import TagLabel

class TagWidget(forms.TextInput):
    def __init__(self, content_type_id = None, *args, **kwargs):
        super(TagWidget, self).__init__(*args, **kwargs)
        self.content_type_id = content_type_id

    def render(self, name, value, attrs=None):
        if not attrs: attrs = { }
        if isinstance(value, list):
            value = ', '.join([ tag_label.label for tag_label in value ])

        js = ''
        if self.content_type_id is not None:
            attrs['onfocus'] = "%s_init(this);" % ( name )
            attrs['autocomplete'] = 'off'
            js = """
<link rel="stylesheet" href="%(media_url)ssphene/community/jqac.css" />
<script language="JavaScript">
<!--
  function %(name)s_get_autocomplete(string, callback) {
    $.get("%(url)s", { content_type_id: "%(content_type_id)d", string: encodeURIComponent(string) },
        function(data) {
          var r=[];
          $(data).find('taglabel').each(function(){
            r.push( { id: $(this).find('id').text(),
                      value: $(this).find('label').text(), } );
          });
          callback( r );
        });
  }
  function %(name)s_init(input) {
    //alert( "content_type_id: %(content_type_id)d" );
    $(input).autocomplete({ ajax_get:%(name)s_get_autocomplete, minchars:1, multi:true });
  }
//-->
</script>""" % { 'name': name, 
                 'media_url': settings.MEDIA_URL, 
                 'content_type_id': self.content_type_id,
                 'url': sph_reverse( 'sph_tags_json_autocompletion', (), {} ), };

        widget = super(TagWidget, self).render(name, value, attrs)
        return "%s%s" % (js, widget)
