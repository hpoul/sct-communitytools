# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Group'
        db.create_table('community_group', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('longname', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('default_theme', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Theme'], null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Group'], null=True, blank=True)),
            ('baseurl', self.gf('django.db.models.fields.CharField')(max_length=250)),
        ))
        db.send_create_signal('community', ['Group'])

        # Adding model 'GroupMember'
        db.create_table('community_groupmember', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Group'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('userlevel', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('community', ['GroupMember'])

        # Adding model 'Theme'
        db.create_table('community_theme', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=250)),
        ))
        db.send_create_signal('community', ['Theme'])

        # Adding model 'Navigation'
        db.create_table('community_navigation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Group'])),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('href', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('urltype', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('sortorder', self.gf('django.db.models.fields.IntegerField')(default=100)),
            ('navigationType', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('community', ['Navigation'])

        # Adding model 'ApplicationChangelog'
        db.create_table('community_applicationchangelog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('app_label', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('model', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('applied', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('community', ['ApplicationChangelog'])

        # Adding model 'CommunityUserProfile'
        db.create_table('community_communityuserprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('displayname', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('public_emailaddress', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('avatar', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('avatar_height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('avatar_width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('community', ['CommunityUserProfile'])

        # Adding model 'CommunityUserProfileField'
        db.create_table('community_communityuserprofilefield', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('help_text', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
            ('regex', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
            ('renderstring', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
            ('sortorder', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('community', ['CommunityUserProfileField'])

        # Adding model 'CommunityUserProfileFieldValue'
        db.create_table('community_communityuserprofilefieldvalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.CommunityUserProfile'])),
            ('profile_field', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.CommunityUserProfileField'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=250)),
        ))
        db.send_create_signal('community', ['CommunityUserProfileFieldValue'])

        # Adding unique constraint on 'CommunityUserProfileFieldValue', fields ['user_profile', 'profile_field']
        db.create_unique('community_communityuserprofilefieldvalue', ['user_profile_id', 'profile_field_id'])

        # Adding model 'GroupTemplate'
        db.create_table('community_grouptemplate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Group'])),
            ('template_name', self.gf('django.db.models.fields.CharField')(max_length=250, db_index=True)),
            ('source', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('community', ['GroupTemplate'])

        # Adding unique constraint on 'GroupTemplate', fields ['group', 'template_name']
        db.create_unique('community_grouptemplate', ['group_id', 'template_name'])

        # Adding model 'PermissionFlag'
        db.create_table('community_permissionflag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=250)),
        ))
        db.send_create_signal('community', ['PermissionFlag'])

        # Adding model 'Role'
        db.create_table('community_role', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Group'])),
        ))
        db.send_create_signal('community', ['Role'])

        # Adding unique constraint on 'Role', fields ['name', 'group']
        db.create_unique('community_role', ['name', 'group_id'])

        # Adding M2M table for field permission_flags on 'Role'
        db.create_table('community_role_permission_flags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('role', models.ForeignKey(orm['community.role'], null=False)),
            ('permissionflag', models.ForeignKey(orm['community.permissionflag'], null=False))
        ))
        db.create_unique('community_role_permission_flags', ['role_id', 'permissionflag_id'])

        # Adding model 'RoleMember'
        db.create_table('community_rolemember', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Role'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('rolegroup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.RoleGroup'], null=True)),
            ('has_limitations', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('community', ['RoleMember'])

        # Adding model 'RoleMemberLimitation'
        db.create_table('community_rolememberlimitation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('role_member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.RoleMember'])),
            ('object_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('community', ['RoleMemberLimitation'])

        # Adding unique constraint on 'RoleMemberLimitation', fields ['role_member', 'object_type', 'object_id']
        db.create_unique('community_rolememberlimitation', ['role_member_id', 'object_type_id', 'object_id'])

        # Adding model 'RoleGroup'
        db.create_table('community_rolegroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Group'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
        ))
        db.send_create_signal('community', ['RoleGroup'])

        # Adding unique constraint on 'RoleGroup', fields ['group', 'name']
        db.create_unique('community_rolegroup', ['group_id', 'name'])

        # Adding model 'RoleGroupMember'
        db.create_table('community_rolegroupmember', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rolegroup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.RoleGroup'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('community', ['RoleGroupMember'])

        # Adding unique constraint on 'RoleGroupMember', fields ['rolegroup', 'user']
        db.create_unique('community_rolegroupmember', ['rolegroup_id', 'user_id'])

        # Adding model 'Tag'
        db.create_table('community_tag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['community.Group'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
        ))
        db.send_create_signal('community', ['Tag'])

        # Adding unique constraint on 'Tag', fields ['group', 'name']
        db.create_unique('community_tag', ['group_id', 'name'])

        # Adding model 'TagLabel'
        db.create_table('community_taglabel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(related_name='labels', to=orm['community.Tag'])),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=250)),
        ))
        db.send_create_signal('community', ['TagLabel'])

        # Adding unique constraint on 'TagLabel', fields ['tag', 'label']
        db.create_unique('community_taglabel', ['tag_id', 'label'])

        # Adding model 'TaggedItem'
        db.create_table('community_taggeditem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tag_label', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['community.TagLabel'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sph_taggeditem_set', to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('community', ['TaggedItem'])

        # Adding unique constraint on 'TaggedItem', fields ['tag_label', 'content_type', 'object_id']
        db.create_unique('community_taggeditem', ['tag_label_id', 'content_type_id', 'object_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'TaggedItem', fields ['tag_label', 'content_type', 'object_id']
        db.delete_unique('community_taggeditem', ['tag_label_id', 'content_type_id', 'object_id'])

        # Removing unique constraint on 'TagLabel', fields ['tag', 'label']
        db.delete_unique('community_taglabel', ['tag_id', 'label'])

        # Removing unique constraint on 'Tag', fields ['group', 'name']
        db.delete_unique('community_tag', ['group_id', 'name'])

        # Removing unique constraint on 'RoleGroupMember', fields ['rolegroup', 'user']
        db.delete_unique('community_rolegroupmember', ['rolegroup_id', 'user_id'])

        # Removing unique constraint on 'RoleGroup', fields ['group', 'name']
        db.delete_unique('community_rolegroup', ['group_id', 'name'])

        # Removing unique constraint on 'RoleMemberLimitation', fields ['role_member', 'object_type', 'object_id']
        db.delete_unique('community_rolememberlimitation', ['role_member_id', 'object_type_id', 'object_id'])

        # Removing unique constraint on 'Role', fields ['name', 'group']
        db.delete_unique('community_role', ['name', 'group_id'])

        # Removing unique constraint on 'GroupTemplate', fields ['group', 'template_name']
        db.delete_unique('community_grouptemplate', ['group_id', 'template_name'])

        # Removing unique constraint on 'CommunityUserProfileFieldValue', fields ['user_profile', 'profile_field']
        db.delete_unique('community_communityuserprofilefieldvalue', ['user_profile_id', 'profile_field_id'])

        # Deleting model 'Group'
        db.delete_table('community_group')

        # Deleting model 'GroupMember'
        db.delete_table('community_groupmember')

        # Deleting model 'Theme'
        db.delete_table('community_theme')

        # Deleting model 'Navigation'
        db.delete_table('community_navigation')

        # Deleting model 'ApplicationChangelog'
        db.delete_table('community_applicationchangelog')

        # Deleting model 'CommunityUserProfile'
        db.delete_table('community_communityuserprofile')

        # Deleting model 'CommunityUserProfileField'
        db.delete_table('community_communityuserprofilefield')

        # Deleting model 'CommunityUserProfileFieldValue'
        db.delete_table('community_communityuserprofilefieldvalue')

        # Deleting model 'GroupTemplate'
        db.delete_table('community_grouptemplate')

        # Deleting model 'PermissionFlag'
        db.delete_table('community_permissionflag')

        # Deleting model 'Role'
        db.delete_table('community_role')

        # Removing M2M table for field permission_flags on 'Role'
        db.delete_table('community_role_permission_flags')

        # Deleting model 'RoleMember'
        db.delete_table('community_rolemember')

        # Deleting model 'RoleMemberLimitation'
        db.delete_table('community_rolememberlimitation')

        # Deleting model 'RoleGroup'
        db.delete_table('community_rolegroup')

        # Deleting model 'RoleGroupMember'
        db.delete_table('community_rolegroupmember')

        # Deleting model 'Tag'
        db.delete_table('community_tag')

        # Deleting model 'TagLabel'
        db.delete_table('community_taglabel')

        # Deleting model 'TaggedItem'
        db.delete_table('community_taggeditem')


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
        'community.applicationchangelog': {
            'Meta': {'object_name': 'ApplicationChangelog'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'applied': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'community.communityuserprofile': {
            'Meta': {'object_name': 'CommunityUserProfile'},
            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'avatar_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'avatar_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'displayname': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public_emailaddress': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'community.communityuserprofilefield': {
            'Meta': {'ordering': "['sortorder']", 'object_name': 'CommunityUserProfileField'},
            'help_text': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'renderstring': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'sortorder': ('django.db.models.fields.IntegerField', [], {})
        },
        'community.communityuserprofilefieldvalue': {
            'Meta': {'unique_together': "(('user_profile', 'profile_field'),)", 'object_name': 'CommunityUserProfileFieldValue'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'profile_field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.CommunityUserProfileField']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.CommunityUserProfile']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '250'})
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
        'community.groupmember': {
            'Meta': {'object_name': 'GroupMember'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'userlevel': ('django.db.models.fields.IntegerField', [], {})
        },
        'community.grouptemplate': {
            'Meta': {'unique_together': "(('group', 'template_name'),)", 'object_name': 'GroupTemplate'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.TextField', [], {}),
            'template_name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'db_index': 'True'})
        },
        'community.navigation': {
            'Meta': {'ordering': "['sortorder']", 'object_name': 'Navigation'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Group']"}),
            'href': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'navigationType': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'sortorder': ('django.db.models.fields.IntegerField', [], {'default': '100'}),
            'urltype': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'community.permissionflag': {
            'Meta': {'object_name': 'PermissionFlag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'})
        },
        'community.role': {
            'Meta': {'unique_together': "(('name', 'group'),)", 'object_name': 'Role'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'permission_flags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'roles'", 'symmetrical': 'False', 'to': "orm['community.PermissionFlag']"})
        },
        'community.rolegroup': {
            'Meta': {'unique_together': "(('group', 'name'),)", 'object_name': 'RoleGroup'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'community.rolegroupmember': {
            'Meta': {'unique_together': "(('rolegroup', 'user'),)", 'object_name': 'RoleGroupMember'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rolegroup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.RoleGroup']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'community.rolemember': {
            'Meta': {'object_name': 'RoleMember'},
            'has_limitations': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Role']"}),
            'rolegroup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.RoleGroup']", 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'community.rolememberlimitation': {
            'Meta': {'unique_together': "(('role_member', 'object_type', 'object_id'),)", 'object_name': 'RoleMemberLimitation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'object_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'role_member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.RoleMember']"})
        },
        'community.tag': {
            'Meta': {'unique_together': "(('group', 'name'),)", 'object_name': 'Tag'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['community.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'community.taggeditem': {
            'Meta': {'unique_together': "(('tag_label', 'content_type', 'object_id'),)", 'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sph_taggeditem_set'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tag_label': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['community.TagLabel']"})
        },
        'community.taglabel': {
            'Meta': {'unique_together': "(('tag', 'label'),)", 'object_name': 'TagLabel'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'labels'", 'to': "orm['community.Tag']"})
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
        }
    }

    complete_apps = ['community']
