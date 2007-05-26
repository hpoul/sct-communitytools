from django.db import models

from django.contrib.auth.models import User
#from django.db.models import permalink
from sphene.community.sphutils import sphpermalink as permalink

from sphene.community.models import Group

from datetime import datetime

from sphene.community.middleware import get_current_request, get_current_user

"""
def permalink(func):
    from django.core.urlresolvers import reverse
    from django.conf import settings
    def inner(*args, **kwargs):
        bits = func(*args, **kwargs)
        viewname = bits[0]
        req = get_current_request()
        urlconf = getattr(req, 'urlconf', settings.ROOT_URLCONF)
        return reverse(bits[0], urlconf, *bits[1:3])
    return inner
"""

WIKI_PERMISSIONS_ALLOWED_CHOICES = (
    (-1, 'All Users'),
    (0, 'Loggedin Users'),
    (1, 'Members of the Group'),
    (2, 'Staff Members'),
    (3, 'Nobody'),
    )


class WikiSnip(models.Model):
    name = models.CharField(maxlength = 250, editable = False)
    title = models.CharField(maxlength = 250, blank = True)
    group = models.ForeignKey(Group, editable = False)
    body = models.TextField()
    creator = models.ForeignKey(User, related_name = 'wikisnip_created', editable = False, null = True, blank = True)
    created = models.DateTimeField(editable = False)
    editor  = models.ForeignKey(User, related_name = 'wikisnip_edited', editable = False, null = True, blank = True)
    changed = models.DateTimeField(editable = False)

    changelog = ( ( '2007-04-08 00', 'alter', 'ALTER creator_id DROP NOT NULL', ),
                  ( '2007-04-08 01', 'alter', 'ALTER editor_id DROP NOT NULL', ),
                  )

    def save(self):
        if not self.id:
            self.created = datetime.today()
            self.creator = self.editor
        self.changed = datetime.today()
        super(WikiSnip, self).save()

    def __str__(self):
        if not self.group: return self.name;
        return '%s (%s)' % (self.name, self.group.name)

    def get_absolute_url(self):
        return ('sphene.sphwiki.views.showSnip', (), { 'groupName': self.group.name, 'snipName': self.name })
    get_absolute_url = permalink(get_absolute_url, get_current_request)

    def get_absolute_editurl(self):
        return ('sphene.sphwiki.views.editSnip', (), { 'groupName': self.group.name, 'snipName': self.name })
    get_absolute_editurl = permalink(get_absolute_editurl, get_current_request)

    def get_absolute_attachmenturl(self):
        return ('sphene.sphwiki.views.attachment', (), { 'groupName': self.group.name, 'snipName': self.name })
    get_absolute_attachmenturl = permalink(get_absolute_attachmenturl, get_current_request)

    def get_absolute_historyurl(self):
        return ('sphene.sphwiki.views.history', (), { 'groupName': self.group.name, 'snipName': self.name})
    get_absolute_historyurl = permalink(get_absolute_historyurl, get_current_request)

    def get_absolute_recentchangesurl(self):
        return ('sphene.sphwiki.views.recentChanges', (), { 'groupName': self.group.name })
    get_absolute_recentchangesurl = permalink(get_absolute_recentchangesurl, get_current_request)

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

        if user.is_superuser: return True

        if permission == 0: return True

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

    class Admin:
        list_display = ('name', 'group', 'title', 'changed', )
        list_filter = ('group',)


class WikiSnipChange(models.Model):
    snip = models.ForeignKey(WikiSnip)
    editor = models.ForeignKey(User, null = True, blank = True)
    edited = models.DateTimeField()
    body = models.TextField()
    message = models.TextField()

    changelog = ( ( '2007-04-08 00', 'alter', 'ALTER editor_id DROP NOT NULL', ),
                  )

    def get_absolute_url(self):
        return ('sphene.sphwiki.views.diff', (), { 'groupName': self.snip.group.name, 'snipName': self.snip.name, 'changeId': self.id})
    get_absolute_url = permalink(get_absolute_url, get_current_request)


class WikiPreference(models.Model):
    snip = models.ForeignKey(WikiSnip, edit_inline = models.STACKED, max_num_in_admin = 1)
    view = models.IntegerField( choices = WIKI_PERMISSIONS_ALLOWED_CHOICES, core = True )
    edit = models.IntegerField( choices = WIKI_PERMISSIONS_ALLOWED_CHOICES, core = True )

    class Admin:
        list_display = ( 'snip', 'view', 'edit' )

class WikiAttachment(models.Model):
    snip = models.ForeignKey(WikiSnip, editable = False)
    uploader = models.ForeignKey(User, editable = False)
    uploaded = models.DateTimeField(editable = False)
    fileupload = models.FileField( upload_to = 'var/sphene/sphwiki/attachment/%Y/%m/%d' )
    description = models.TextField()

    def save(self):
        self.uploaded = datetime.today()
        super(WikiAttachment, self).save()

    def __str__(self):
        return self.fileupload

    class Admin:
        pass



