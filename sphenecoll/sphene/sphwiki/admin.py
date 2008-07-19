from django.contrib import admin

from sphene.sphwiki import models


class WikiSnipAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'title', 'changed', )
    list_filter = ('group',)

admin.site.register(models.WikiSnip, WikiSnipAdmin)

class WikiPreferenceAdmin(admin.ModelAdmin):
    list_display = ( 'snip', 'view', 'edit' )

admin.site.register(models.WikiPreference, WikiPreferenceAdmin)
admin.site.register(models.WikiAttachment)
