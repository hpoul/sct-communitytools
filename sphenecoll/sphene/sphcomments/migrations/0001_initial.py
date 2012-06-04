# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CommentsCategoryConfig'
        db.create_table('sphcomments_commentscategoryconfig', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sphcomments_config', unique=True, to=orm['sphboard.Category'])),
            ('object_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('sphcomments', ['CommentsCategoryConfig'])

        # Adding unique constraint on 'CommentsCategoryConfig', fields ['category', 'object_type', 'object_id']
        db.create_unique('sphcomments_commentscategoryconfig', ['category_id', 'object_type_id', 'object_id'])

    def backwards(self, orm):
        # Removing unique constraint on 'CommentsCategoryConfig', fields ['category', 'object_type', 'object_id']
        db.delete_unique('sphcomments_commentscategoryconfig', ['category_id', 'object_type_id', 'object_id'])

        # Deleting model 'CommentsCategoryConfig'
        db.delete_table('sphcomments_commentscategoryconfig')

    models = {
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
        'sphcomments.commentscategoryconfig': {
            'Meta': {'unique_together': "(('category', 'object_type', 'object_id'),)", 'object_name': 'CommentsCategoryConfig'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sphcomments_config'", 'unique': 'True', 'to': "orm['sphboard.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'object_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"})
        }
    }

    complete_apps = ['sphcomments']