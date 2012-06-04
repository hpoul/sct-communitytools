# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PageConfiguration'
        db.create_table('sphblockframework_pageconfiguration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Group'])),
            ('user_configurable', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('sphblockframework', ['PageConfiguration'])

        # Adding model 'PageConfigurationInstance'
        db.create_table('sphblockframework_pageconfigurationinstance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page_configuration', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphblockframework.PageConfiguration'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
        ))
        db.send_create_signal('sphblockframework', ['PageConfigurationInstance'])

        # Adding unique constraint on 'PageConfigurationInstance', fields ['page_configuration', 'user']
        db.create_unique('sphblockframework_pageconfigurationinstance', ['page_configuration_id', 'user_id'])

        # Adding model 'BlockRegion'
        db.create_table('sphblockframework_blockregion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('config_instance', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphblockframework.PageConfigurationInstance'])),
        ))
        db.send_create_signal('sphblockframework', ['BlockRegion'])

        # Adding model 'BlockConfiguration'
        db.create_table('sphblockframework_blockconfiguration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page_configuration', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphblockframework.PageConfiguration'])),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
            ('block_name', self.gf('django.db.models.fields.CharField')(max_length=250, db_index=True)),
            ('config_value', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
        ))
        db.send_create_signal('sphblockframework', ['BlockConfiguration'])

        # Adding model 'BlockInstancePosition'
        db.create_table('sphblockframework_blockinstanceposition', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphblockframework.BlockRegion'])),
            ('block_configuration', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphblockframework.BlockConfiguration'])),
            ('sortorder', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('sphblockframework', ['BlockInstancePosition'])

    def backwards(self, orm):
        # Removing unique constraint on 'PageConfigurationInstance', fields ['page_configuration', 'user']
        db.delete_unique('sphblockframework_pageconfigurationinstance', ['page_configuration_id', 'user_id'])

        # Deleting model 'PageConfiguration'
        db.delete_table('sphblockframework_pageconfiguration')

        # Deleting model 'PageConfigurationInstance'
        db.delete_table('sphblockframework_pageconfigurationinstance')

        # Deleting model 'BlockRegion'
        db.delete_table('sphblockframework_blockregion')

        # Deleting model 'BlockConfiguration'
        db.delete_table('sphblockframework_blockconfiguration')

        # Deleting model 'BlockInstancePosition'
        db.delete_table('sphblockframework_blockinstanceposition')

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
        'sphblockframework.blockconfiguration': {
            'Meta': {'object_name': 'BlockConfiguration'},
            'block_name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'db_index': 'True'}),
            'config_value': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'page_configuration': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphblockframework.PageConfiguration']"})
        },
        'sphblockframework.blockinstanceposition': {
            'Meta': {'ordering': "['sortorder']", 'object_name': 'BlockInstancePosition'},
            'block_configuration': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphblockframework.BlockConfiguration']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphblockframework.BlockRegion']"}),
            'sortorder': ('django.db.models.fields.IntegerField', [], {})
        },
        'sphblockframework.blockregion': {
            'Meta': {'object_name': 'BlockRegion'},
            'config_instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphblockframework.PageConfigurationInstance']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'sphblockframework.pageconfiguration': {
            'Meta': {'object_name': 'PageConfiguration'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user_configurable': ('django.db.models.fields.IntegerField', [], {})
        },
        'sphblockframework.pageconfigurationinstance': {
            'Meta': {'unique_together': "(('page_configuration', 'user'),)", 'object_name': 'PageConfigurationInstance'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page_configuration': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphblockframework.PageConfiguration']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        }
    }

    complete_apps = ['sphblockframework']