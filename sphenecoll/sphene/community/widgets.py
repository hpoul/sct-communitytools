from django import forms
from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe

from sphene.community.templatetags.sph_extras import sph_basename
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
                      value: $(this).find('label').text() } );
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
                 'media_url': settings.STATIC_URL, 
                 'content_type_id': self.content_type_id,
                 'url': sph_reverse( 'sph_tags_json_autocompletion', (), {} ), };

        widget = super(TagWidget, self).render(name, value, attrs)
        return "%s%s" % (js, widget)

class SPHFileWidget(forms.FileInput):
    """
    A FileField Widget that shows its current value if it has one.
    Based on AdminFileWidget
    """
    def __init__(self, attrs={}):
        super(SPHFileWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        output = []
        if value and hasattr(value, "url"):
            output.append('<div class="current-sphfile">%s <a target="_blank" href="%s">%s</a> (%s)</div> %s ' % \
                (_('Currently:'), value.url, sph_basename(value.url), filesizeformat(value.size), _('Change:')))
        output.append(super(SPHFileWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))
