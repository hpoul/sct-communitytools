from django.contrib import admin

from sphene.sphwiki import models

class WikiPreferenceInline(admin.TabularInline):
    model = models.WikiPreference
    max_num = 1


class WikiSnipAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'title', 'changed', )
    list_filter = ('group',)
    fieldsets = (
        ( 'Basics', {
                'description': 'You should not create or edit wiki snips through the django admin page. (Except for permissions.)',
                'fields': ('name', 'title', 'group', 'body', ),
                }),
        )
    inlines = [ WikiPreferenceInline, ]

admin.site.register(models.WikiSnip, WikiSnipAdmin)

class WikiPreferenceAdmin(admin.ModelAdmin):
    list_display = ( 'snip', 'view', 'edit' )

admin.site.register(models.WikiPreference, WikiPreferenceAdmin)

class WikiAttachmentAdmin(admin.ModelAdmin):
    list_display = ( 'uploader', 'fileupload', 'snip', )

admin.site.register(models.WikiAttachment, WikiAttachmentAdmin)
