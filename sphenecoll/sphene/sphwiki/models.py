from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext, ugettext_lazy


from sphene.community.templatetags.sph_extras import sph_markdown
#from django.db.models import permalink
from sphene.community.sphutils import sphpermalink, get_sph_setting, sph_reverse

from sphene.community.models import Group

from datetime import datetime

from sphene.community.middleware import get_current_request, get_current_user

import os
import re

WIKI_PERMISSIONS_ALLOWED_CHOICES = (
    (-1, 'All Users'),
    (0, 'Loggedin Users'),
    (1, 'Members of the Group'),
    (2, 'Staff Members'),
    (3, 'Nobody'),
    )


class WikiSnip(models.Model):
    name = models.CharField(ugettext_lazy('name'), max_length = 250)
    title = models.CharField(ugettext_lazy('title'), max_length = 250, blank = True)
    group = models.ForeignKey(Group)
    body = models.TextField(ugettext_lazy('body'))
    creator = models.ForeignKey(User, related_name = 'wikisnip_created', editable = False, null = True, blank = True)
    created = models.DateTimeField(editable = False)
    editor  = models.ForeignKey(User, related_name = 'wikisnip_edited', editable = False, null = True, blank = True)
    changed = models.DateTimeField(editable = False)

    changelog = ( ( '2007-04-08 00', 'alter', 'ALTER creator_id DROP NOT NULL', ),
                  ( '2007-04-08 01', 'alter', 'ALTER editor_id DROP NOT NULL', ),
                  )

    def render(self):
        from sphene.sphwiki import wikimacros
        return mark_safe(sph_markdown(self.body,
                            extra_macros = { 'attachmentlist': wikimacros.AttachmentListMacro( snip = self, ),
                                             'attachment': wikimacros.AttachmentMacro( snip = self, ),
                                             'img': wikimacros.ImageMacro( ),
                                             'redirect': wikimacros.RedirectMacro( ),
                                             }))

    def get_title(self):
        return self.title or self.name

    def pdf_get_cachefile(self):
        """ Returns the pathname to the cache file for this wiki snip. """
        if not get_sph_setting( 'wiki_pdf_generation', False ) or not self.pdf_enabled():
            raise Exception('PDF Generation not enabled by configuration.')
        
        cachedir = get_sph_setting( 'wiki_pdf_generation_cachedir', '/tmp/sct_pdf' )
        
        if not os.path.isdir( cachedir ):
            os.mkdir( cachedir )

        filename = re.sub("[^A-Za-z0-9]", "_", self.name)
        cachefile = os.path.join( cachedir, '%s_%d.pdf' % (filename, self.id) )

        return cachefile

    def pdf_needs_regenerate(self):
        """ Determines if the PDF cachefile needs to be regenerated. """
        cachefile = self.pdf_get_cachefile()
        
        if not os.path.isfile( cachefile ):
            return True
        
        # Check if cache file is older than last modification of wiki snip.
        modifytime = datetime.fromtimestamp(os.path.getmtime( cachefile ))
        if modifytime < self.changed:
            return True
        return False

    def pdf_generate(self):
        """ Generates the PDF for this snip and stores it into cachedir. """
        cachefile = self.pdf_get_cachefile()
        xmlfile = cachefile + '.xhtml'

        snip_rendered_body = str(self.render()) # TODO do this in the model ? like the board post body ?
        sctpath = hasattr(settings,'LIB_PATH') and settings.LIB_PATH or '.'
        #static_filepath = get_sph_setting( 'wiki_pdf_generation_static_filepath', os.path.join(sctpath, '..', 'static', 'sphene') )
	static_filepath = settings.MEDIA_ROOT
        snip_rendered_body = snip_rendered_body.replace( 
            '<img src="%(media_url)s' % \
                { 'media_url': settings.STATIC_URL },
            '<img src="%s/' % static_filepath )
        import codecs
        xmlout = codecs.open(xmlfile, mode='w', encoding='utf-8')

        xmlout.write('''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>%(title)s</title>
  </head>
  <body>
  <div id="header" class="pdf">
    <div class="label">%(title)s</div>
  </div>
  <div id="footer" class="pdf">
    Page
       <pdf:pagenumber />
  </div>

  ''' % { 'title': self.title or self.name } )
        xmlout.write(snip_rendered_body)
        xmlout.write('''
  </body>
</html>
''')
        
        xmlout.close()
        
        command = get_sph_setting('wiki_pdf_generation_command')
        os.system( command % { 'srcfile': xmlfile, 'destfile': cachefile, } )
        if not os.path.isfile( cachefile ):
            raise Exception( 'Error while generating PDF.' )

    def pdf_get(self):
        """
        Returns the pathname to the generated PDF. - If a regeneration is
        necessary it is done.
        Raises an Exception if anything goes wrong.
        """
        if self.pdf_needs_regenerate():
            self.pdf_generate()

        cachefile = self.pdf_get_cachefile()

        return cachefile

    def pdf_enabled(self):
        """
        Checks if PDF generation is 1. enabled and 2. the current user has
        permission. (E.g. setting 'wiki_pdf_generation' to 'loggedin' would
        only allow loggedin users to view PDF versions.)
        This method is ment to be used in templates.
        """
        setting = get_sph_setting('wiki_pdf_generation')
        if setting == True:
            return True
        if setting == 'loggedin':
            return get_current_user() and get_current_user().is_authenticated()
        if setting == 'staff':
            return get_current_user() and get_current_user().is_authenticated() and get_current_user().is_staff

        return False

    def save(self, force_insert=False, force_update=False):
        if not self.id:
            self.created = datetime.today()
            self.creator = self.editor
        self.changed = datetime.today()
        super(WikiSnip, self).save(force_insert=force_insert, force_update=force_update)

    def __unicode__(self):
        if not self.group: return self.name;
        return '%s (%s)' % (self.name, self.group.name)

    def get_absolute_url(self):
        return ('sphene.sphwiki.views.showSnip', (), { 'groupName': self.group.name, 'snipName': self.name })
    get_absolute_url = sphpermalink(get_absolute_url)

    def get_absolute_editurl(self):
        return ('sphene.sphwiki.views.editSnip', (), { 'groupName': self.group.name, 'snipName': self.name })
    get_absolute_editurl = sphpermalink(get_absolute_editurl)

    def get_absolute_attachmenturl(self):
        return ('sphene.sphwiki.views.attachment', (), { 'groupName': self.group.name, 'snipName': self.name })
    get_absolute_attachmenturl = sphpermalink(get_absolute_attachmenturl)

    def get_absolute_create_attachmenturl(self):
        return ('sphene.sphwiki.views.attachmentCreate', (), { 'groupName': self.group.name, 'snipName': self.name })
    get_absolute_create_attachmenturl = sphpermalink(get_absolute_create_attachmenturl)

    def get_absolute_historyurl(self):
        return ('sphene.sphwiki.views.history', (), { 'groupName': self.group.name, 'snipName': self.name})
    get_absolute_historyurl = sphpermalink(get_absolute_historyurl)

    def get_absolute_recentchangesurl(self):
        return ('sphene.sphwiki.views.recentChanges', (), { 'groupName': self.group.name })
    get_absolute_recentchangesurl = sphpermalink(get_absolute_recentchangesurl)

    def get_absolute_pdfurl(self):
        return ('sphene.sphwiki.views.generatePDF', (), { 'groupName': self.group.name, 'snipName': self.name })
    get_absolute_pdfurl = sphpermalink(get_absolute_pdfurl)

    def get_parent(self):
        lastslash = len(self.name)
        while lastslash != -1:
            lastslash = self.name.rfind( '/', 0, lastslash )
            if lastslash == -1:
                if self.name == 'ROOT': return None
                name = 'ROOT'
            else:
                name = self.name[:lastslash]

            try:
                return WikiSnip.objects.get( group = self.group,
                                             name__exact = name,)
            except WikiSnip.DoesNotExist:
                pass
        
        return None

    def get_snip_path(self):
        path = self.name.split( '/' )
        snip_path = []
        lastsnip = None
        for element in path:
            if lastsnip is not None:
                snipname = lastsnip + '/' + element;
            else:
                snipname = element

            try:
                snip = WikiSnip.objects.get( group = self.group,
                                             name__exact = snipname, )
            except WikiSnip.DoesNotExist:
                snip = None
            snip_path.append( { 'name': element, 'snip': snip, } )

            lastsnip = snipname

        return snip_path

    def is_secured(self):
        pref = self.get_wiki_preference()
        return pref != None and pref.view > -1

    def get_wiki_preference(self):
        if hasattr(self, '_wiki_preference'): return self._wiki_preference
        self._wiki_preference = self.__get_wiki_preference()
        return self._wiki_preference
    
    def __get_wiki_preference(self):
        try:
            return WikiPreference.objects.get( snip = self )
        except WikiPreference.DoesNotExist:
            parent = self.get_parent()
            if parent == None:
                return None
            return parent.get_wiki_preference()

    def __has_permission(self, user, pref, permission):
        if permission == None or permission <= -1:
            return True

        if user == None or not user.is_authenticated():
            return False

        # Noone has permission ..
        if permission >= 3: return False

        if user.is_superuser or user.is_staff: return True

        if permission == 0: return True

        # if pref is None check for the group of the current snip.
        if permission == 1 and pref == None and self.group.get_member(user) != None:
            return True

        if permission == 1 and pref != None and pref.snip != None:
            if pref.snip.group.get_member(user) != None: return True

        return False

    def has_edit_permission(self):
        user = get_current_user()
        pref = self.get_wiki_preference()
        if pref == None:
            # By default only members of the group are allowed to edit posts
            # TODO don't hardcode this, but make it configurable ..
            # (it actually is.. by creating a 'ROOT' wiki snip)
            permission = 1 
        else:
            permission = pref.edit
        return self.__has_permission(user, pref, permission)

    def has_view_permission(self):
        user = get_current_user()
        pref = self.get_wiki_preference()
        return pref == None or self.__has_permission(user, pref, pref.view)


class WikiSnipChange(models.Model):
    snip = models.ForeignKey(WikiSnip)
    editor = models.ForeignKey(User, null = True, blank = True)
    edited = models.DateTimeField()
    title = models.CharField(max_length = 250, blank = True)
    body = models.TextField()
    message = models.TextField()

    # Change type is a bit flag of:
    # 1 = body changed
    # 2 = title changed
    # 4 = tags changed
    # use the the methods: body_changed(), title_changed(), tags_changed()
    # to check what has changed.
    change_type = models.IntegerField()

    changelog = ( ( '2007-04-08 00', 'alter', 'ALTER editor_id DROP NOT NULL', ),
                  ( '2008-03-23 00', 'alter', 'ADD title VARCHAR(250)', ),
                  ( '2008-03-23 01', 'update', "SET title = ''", ),
                  ( '2008-03-23 02', 'alter', 'ALTER title SET NOT NULL', ),
                  ( '2008-03-23 03', 'alter', 'ADD change_type INTEGER', ),
                  ( '2008-03-23 04', 'update', 'SET change_type = 0', ),
                  ( '2008-03-23 05', 'alter', 'ALTER change_type SET NOT NULL', ),
                  )

    def body_changed(self):
        return self.change_type & 1

    def title_changed(self):
        return self.change_type & 2

    def tags_changed(self):
        return self.change_type & 4

    def get_absolute_url(self):
        return ('sphene.sphwiki.views.diff', (), { 'groupName': self.snip.group.name, 'snipName': self.snip.name, 'changeId': self.id})
    get_absolute_url = sphpermalink(get_absolute_url)

    def get_absolute_editurl(self):
        return sph_reverse( 'sphwiki_editversion', 
                            kwargs = { 'snipName': self.snip.name,
                                       'versionId': self.id } );


class WikiPreference(models.Model):
    snip = models.ForeignKey(WikiSnip)
    view = models.IntegerField( choices = WIKI_PERMISSIONS_ALLOWED_CHOICES )
    edit = models.IntegerField( choices = WIKI_PERMISSIONS_ALLOWED_CHOICES )


class WikiAttachment(models.Model):
    snip = models.ForeignKey(WikiSnip, editable = False)
    uploader = models.ForeignKey(User, editable = False)
    uploaded = models.DateTimeField(editable = False)
    fileupload = models.FileField( ugettext_lazy('fileupload'),
                                   upload_to = get_sph_setting( 'wiki_attachments_upload_to' ) )
    description = models.TextField( ugettext_lazy('description'),
                                    blank=True)

    def get_absolute_editurl(self):
        return ('sphene.sphwiki.views.attachmentEdit', (), { 'groupName': self.snip.group.name, 'snipName': self.snip.name, 'attachmentId': self.id } )
    get_absolute_editurl = sphpermalink(get_absolute_editurl)

    def save(self, force_insert=False, force_update=False):
        self.uploaded = datetime.today()
        super(WikiAttachment, self).save(force_insert=force_insert, force_update=force_update)

    def __unicode__(self):
        return self.fileupload.name




