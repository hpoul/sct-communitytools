# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    depends_on = (
        ("sphene.community", "0001_initial"),
    )

    def forwards(self, orm):
        
        # Adding model 'Category'
        db.create_table('sphboard_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Group'], null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='subcategories', null=True, to=orm['sphboard.Category'])),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('allowview', self.gf('django.db.models.fields.IntegerField')(default=-1)),
            ('allowthreads', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('allowreplies', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('sortorder', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('slug', self.gf('django.db.models.fields.CharField')(unique=True, max_length=250, db_index=True)),
            ('category_type', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=250, blank=True)),
        ))
        db.send_create_signal('sphboard', ['Category'])

        # Adding model 'ThreadLastVisit'
        db.create_table('sphboard_threadlastvisit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('lastvisit', self.gf('django.db.models.fields.DateTimeField')()),
            ('thread', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphboard.Post'])),
        ))
        db.send_create_signal('sphboard', ['ThreadLastVisit'])

        # Adding unique constraint on 'ThreadLastVisit', fields ['user', 'thread']
        db.create_unique('sphboard_threadlastvisit', ['user_id', 'thread_id'])

        # Adding model 'CategoryLastVisit'
        db.create_table('sphboard_categorylastvisit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('lastvisit', self.gf('django.db.models.fields.DateTimeField')()),
            ('oldlastvisit', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphboard.Category'])),
        ))
        db.send_create_signal('sphboard', ['CategoryLastVisit'])

        # Adding unique constraint on 'CategoryLastVisit', fields ['user', 'category']
        db.create_unique('sphboard_categorylastvisit', ['user_id', 'category_id'])

        # Adding model 'Post'
        db.create_table('sphboard_post', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='posts', to=orm['sphboard.Category'])),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('thread', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphboard.Post'], null=True)),
            ('postdate', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='sphboard_post_author_set', null=True, to=orm['auth.User'])),
            ('markup', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('is_hidden', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
        ))
        db.send_create_signal('sphboard', ['Post'])

        # Adding model 'PostAttachment'
        db.create_table('sphboard_postattachment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('post', self.gf('django.db.models.fields.related.ForeignKey')(related_name='attachments', to=orm['sphboard.Post'])),
            ('fileupload', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('sphboard', ['PostAttachment'])

        # Adding model 'PostAnnotation'
        db.create_table('sphboard_postannotation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('post', self.gf('django.db.models.fields.related.ForeignKey')(related_name='annotation', unique=True, to=orm['sphboard.Post'])),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('hide_post', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('markup', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
        ))
        db.send_create_signal('sphboard', ['PostAnnotation'])

        # Adding model 'ThreadInformation'
        db.create_table('sphboard_threadinformation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('root_post', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphboard.Post'])),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphboard.Category'])),
            ('thread_type', self.gf('django.db.models.fields.IntegerField')()),
            ('heat', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('heat_calculated', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('sticky_value', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('latest_post', self.gf('django.db.models.fields.related.ForeignKey')(related_name='thread_latest_set', to=orm['sphboard.Post'])),
            ('post_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('view_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('thread_latest_postdate', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
        ))
        db.send_create_signal('sphboard', ['ThreadInformation'])

        # Adding model 'Monitor'
        db.create_table('sphboard_monitor', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('thread', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphboard.Post'], null=True, blank=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphboard.Category'], null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Group'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('sphboard', ['Monitor'])

        # Adding model 'Poll'
        db.create_table('sphboard_poll', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('post', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphboard.Post'])),
            ('question', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('choices_per_user', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('sphboard', ['Poll'])

        # Adding model 'PollChoice'
        db.create_table('sphboard_pollchoice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphboard.Poll'])),
            ('choice', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('count', self.gf('django.db.models.fields.IntegerField')()),
            ('sortorder', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('sphboard', ['PollChoice'])

        # Adding model 'PollVoters'
        db.create_table('sphboard_pollvoters', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphboard.Poll'])),
            ('choice', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphboard.PollChoice'], null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('sphboard', ['PollVoters'])

        # Adding model 'BoardUserProfile'
        db.create_table('sphboard_boarduserprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('signature', self.gf('django.db.models.fields.TextField')(default='')),
            ('markup', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('default_notifyme_value', self.gf('django.db.models.fields.NullBooleanField')(null=True)),
        ))
        db.send_create_signal('sphboard', ['BoardUserProfile'])

        # Adding model 'UserPostCount'
        db.create_table('sphboard_userpostcount', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Group'], null=True)),
            ('post_count', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('sphboard', ['UserPostCount'])

        # Adding unique constraint on 'UserPostCount', fields ['user', 'group']
        db.create_unique('sphboard_userpostcount', ['user_id', 'group_id'])

        # Adding model 'ExtendedCategoryConfig'
        db.create_table('sphboard_extendedcategoryconfig', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sphboard.Category'], unique=True)),
            ('subject_label', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
            ('body_label', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
            ('body_initial', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('body_help_text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('post_new_thread_label', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
            ('above_thread_list_block', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('sphboard', ['ExtendedCategoryConfig'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'UserPostCount', fields ['user', 'group']
        db.delete_unique('sphboard_userpostcount', ['user_id', 'group_id'])

        # Removing unique constraint on 'CategoryLastVisit', fields ['user', 'category']
        db.delete_unique('sphboard_categorylastvisit', ['user_id', 'category_id'])

        # Removing unique constraint on 'ThreadLastVisit', fields ['user', 'thread']
        db.delete_unique('sphboard_threadlastvisit', ['user_id', 'thread_id'])

        # Deleting model 'Category'
        db.delete_table('sphboard_category')

        # Deleting model 'ThreadLastVisit'
        db.delete_table('sphboard_threadlastvisit')

        # Deleting model 'CategoryLastVisit'
        db.delete_table('sphboard_categorylastvisit')

        # Deleting model 'Post'
        db.delete_table('sphboard_post')

        # Deleting model 'PostAttachment'
        db.delete_table('sphboard_postattachment')

        # Deleting model 'PostAnnotation'
        db.delete_table('sphboard_postannotation')

        # Deleting model 'ThreadInformation'
        db.delete_table('sphboard_threadinformation')

        # Deleting model 'Monitor'
        db.delete_table('sphboard_monitor')

        # Deleting model 'Poll'
        db.delete_table('sphboard_poll')

        # Deleting model 'PollChoice'
        db.delete_table('sphboard_pollchoice')

        # Deleting model 'PollVoters'
        db.delete_table('sphboard_pollvoters')

        # Deleting model 'BoardUserProfile'
        db.delete_table('sphboard_boarduserprofile')

        # Deleting model 'UserPostCount'
        db.delete_table('sphboard_userpostcount')

        # Deleting model 'ExtendedCategoryConfig'
        db.delete_table('sphboard_extendedcategoryconfig')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
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
            'default_notifyme_value': ('django.db.models.fields.NullBooleanField', [], {'null': 'True'}),
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
            'lastvisit': ('django.db.models.fields.DateTimeField', [], {}),
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
            'fileupload': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
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
            'lastvisit': ('django.db.models.fields.DateTimeField', [], {}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sphboard.Post']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sphboard.userpostcount': {
            'Meta': {'unique_together': "(('user', 'group'),)", 'object_name': 'UserPostCount'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Group']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['sphboard']
