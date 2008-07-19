from django.contrib import admin

from sphene.community import models

admin.site.register(models.Group)

class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('group', 'user',)
    list_filter = ('group',)

admin.site.register(models.GroupMember, GroupMemberAdmin)
admin.site.register(models.Theme)

class NavigationAdmin(admin.ModelAdmin):
    list_display = ( 'label', 'group', 'href', 'navigationType', 'sortorder' )
    list_filter = ( 'group', 'navigationType' )
    ordering = ['group', 'navigationType', 'sortorder']

admin.site.register(models.Navigation, NavigationAdmin)


class CommunityUserProfileFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'regex', 'renderstring', 'sortorder', )

admin.site.register(models.CommunityUserProfileField,
                    CommunityUserProfileFieldAdmin)


class GroupTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_name', 'group')
    list_filter = ( 'group', 'template_name' )

admin.site.register(models.GroupTemplate,
                    GroupTemplateAdmin)


class RoleAdmin(admin.ModelAdmin):
    ordering = ('group__id', 'name')

admin.site.register(models.Role, RoleAdmin)

admin.site.register(models.RoleMember)

