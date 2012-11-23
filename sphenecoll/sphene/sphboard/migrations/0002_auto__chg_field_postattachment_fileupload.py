# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'PostAttachment.fileupload'
        db.alter_column('sphboard_postattachment', 'fileupload', self.gf('django.db.models.fields.files.FileField')(max_length=200))

    def backwards(self, orm):

        # Changing field 'PostAttachment.fileupload'
        db.alter_column('sphboard_postattachment', 'fileupload', self.gf('django.db.models.fields.files.FileField')(max_length=100))

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
        'sphboard.boarduserprofile': {
            'Meta': {'object_name': 'BoardUserProfile'},
            'default_notifyme_value': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'markup': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'signature': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'sphboard.category': {
            'Meta': {'ordering': "['sortorder']", 'object_name': 'Category'},
            'allowreplies': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'allowthreads': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'allowview': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'category_type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '250', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subcategories'", 'null': 'True', 'to': "orm['sphboard.Category']"}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250', 'db_index': 'True'}),
            'sortorder': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'sphboard.categorylastvisit': {
            'Meta': {'unique_together': "(('user', 'category'),)", 'object_name': 'CategoryLastVisit'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphboard.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastvisit': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'oldlastvisit': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sphboard.extendedcategoryconfig': {
            'Meta': {'object_name': 'ExtendedCategoryConfig'},
            'above_thread_list_block': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'body_help_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'body_initial': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'body_label': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphboard.Category']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post_new_thread_label': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'subject_label': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'})
        },
        'sphboard.monitor': {
            'Meta': {'object_name': 'Monitor'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphboard.Category']", 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphboard.Post']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sphboard.poll': {
            'Meta': {'object_name': 'Poll'},
            'choices_per_user': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphboard.Post']"}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'sphboard.pollchoice': {
            'Meta': {'ordering': "['sortorder']", 'object_name': 'PollChoice'},
            'choice': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphboard.Poll']"}),
            'sortorder': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'sphboard.pollvoters': {
            'Meta': {'object_name': 'PollVoters'},
            'choice': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphboard.PollChoice']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphboard.Poll']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sphboard.post': {
            'Meta': {'object_name': 'Post'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'sphboard_post_author_set'", 'null': 'True', 'to': "orm['auth.User']"}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': "orm['sphboard.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_hidden': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'markup': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'postdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphboard.Post']", 'null': 'True'})
        },
        'sphboard.postannotation': {
            'Meta': {'object_name': 'PostAnnotation'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'hide_post': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'markup': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'annotation'", 'unique': 'True', 'to': "orm['sphboard.Post']"})
        },
        'sphboard.postattachment': {
            'Meta': {'object_name': 'PostAttachment'},
            'fileupload': ('django.db.models.fields.files.FileField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': "orm['sphboard.Post']"})
        },
        'sphboard.threadinformation': {
            'Meta': {'object_name': 'ThreadInformation'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphboard.Category']"}),
            'heat': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'heat_calculated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latest_post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'thread_latest_set'", 'to': "orm['sphboard.Post']"}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'root_post': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphboard.Post']"}),
            'sticky_value': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'thread_latest_postdate': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'thread_type': ('django.db.models.fields.IntegerField', [], {}),
            'view_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'sphboard.threadlastvisit': {
            'Meta': {'unique_together': "(('user', 'thread'),)", 'object_name': 'ThreadLastVisit'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastvisit': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphboard.Post']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sphboard.userpostcount': {
            'Meta': {'unique_together': "(('user', 'group'),)", 'object_name': 'UserPostCount'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Group']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['sphboard']