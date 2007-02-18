from django.db import models

from django.contrib.auth.models import User

from sphene.community.models import Group

from datetime import datetime


class WikiSnip(models.Model):
    name = models.CharField(maxlength = 250, editable = False)
    title = models.CharField(maxlength = 250, blank = True)
    group = models.ForeignKey(Group, editable = False)
    body = models.TextField()
    creator = models.ForeignKey(User, related_name = 'wikisnip_created', editable = False)
    created = models.DateTimeField(editable = False)
    editor  = models.ForeignKey(User, related_name = 'wikisnip_edited', editable = False)
    changed = models.DateTimeField(editable = False)

    def save(self):
        if not self.id:
            self.created = datetime.today()
            self.creator = self.editor
        self.changed = datetime.today()
        super(WikiSnip, self).save()

    def __str__(self):
        return self.name

    class Admin:
        pass

class WikiAttachment(models.Model):
    snip = models.ForeignKey(Group, editable = False)
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




