from django import newforms as forms


class TagWidget(forms.TextInput):
    def render(self, name, value, attrs=None):
        if not attrs: attrs = { }
        attrs['onfocus'] = "%s_init(this);" % ( name )
        widget = super(TagWidget, self).render(name, value, attrs)
        js = """
<link rel="stylesheet" href="/static/sphene/community/jqac.css" />
<script language="JavaScript">
<!--
  function %(name)s_get_autocomplete(string, callback) {
    callback([ { id:1, value:'asdf' }, { id:2, value:'def' }, { id:3, value:'ghij' }]);
  }
  function %(name)s_init(input) {
/*
TODO this needs to be finished !! ;)
    $(input).autocomplete({ ajax_get:%(name)s_get_autocomplete, minchars:0, multi:true });
*/
  }
//-->
</script>""" % { 'name': name };
        return "%s%s" % (js, widget)
