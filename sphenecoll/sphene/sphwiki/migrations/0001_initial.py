# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'WikiSnip'
        db.create_table('sphwiki_wikisnip', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Group'])),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='wikisnip_created', null=True, to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('editor', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='wikisnip_edited', null=True, to=orm['auth.User'])),
            ('changed', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('sphwiki', ['WikiSnip'])

        # Adding model 'WikiSnipChange'
        db.create_table('sphwiki_wikisnipchange', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('snip', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphwiki.WikiSnip'])),
            ('editor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('edited', self.gf('django.db.models.fields.DateTimeField')()),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('change_type', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('sphwiki', ['WikiSnipChange'])

        # Adding model 'WikiPreference'
        db.create_table('sphwiki_wikipreference', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('snip', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphwiki.WikiSnip'])),
            ('view', self.gf('django.db.models.fields.IntegerField')()),
            ('edit', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('sphwiki', ['WikiPreference'])

        # Adding model 'WikiAttachment'
        db.create_table('sphwiki_wikiattachment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('snip', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphwiki.WikiSnip'])),
            ('uploader', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('uploaded', self.gf('django.db.models.fields.DateTimeField')()),
            ('fileupload', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('sphwiki', ['WikiAttachment'])

    def backwards(self, orm):
        # Deleting model 'WikiSnip'
        db.delete_table('sphwiki_wikisnip')

        # Deleting model 'WikiSnipChange'
        db.delete_table('sphwiki_wikisnipchange')

        # Deleting model 'WikiPreference'
        db.delete_table('sphwiki_wikipreference')

        # Deleting model 'WikiAttachment'
        db.delete_table('sphwiki_wikiattachment')

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'community.group': {
            'Meta': {'object_name': 'Group'},
            'baseurl': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'default_theme': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Theme']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'longname': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Group']", 'null': 'True', 'blank': 'True'})
        },
        'community.theme': {
            'Meta': {'object_name': 'Theme'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sphwiki.wikiattachment': {
            'Meta': {'object_name': 'WikiAttachment'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'fileupload': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'snip': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphwiki.WikiSnip']"}),
            'uploaded': ('django.db.models.fields.DateTimeField', [], {}),
            'uploader': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sphwiki.wikipreference': {
            'Meta': {'object_name': 'WikiPreference'},
            'edit': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'snip': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphwiki.WikiSnip']"}),
            'view': ('django.db.models.fields.IntegerField', [], {})
        },
        'sphwiki.wikisnip': {
            'Meta': {'object_name': 'WikiSnip'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'changed': ('django.db.models.fields.DateTimeField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'wikisnip_created'", 'null': 'True', 'to': "orm['auth.User']"}),
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'wikisnip_edited'", 'null': 'True', 'to': "orm['auth.User']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'})
        },
        'sphwiki.wikisnipchange': {
            'Meta': {'object_name': 'WikiSnipChange'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'change_type': ('django.db.models.fields.IntegerField', [], {}),
            'edited': ('django.db.models.fields.DateTimeField', [], {}),
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'snip': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphwiki.WikiSnip']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'})
        }
    }

    complete_apps = ['sphwiki']