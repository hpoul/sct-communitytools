from django.contrib import admin

from sphene.sphboard import models


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'parent', 'allowview', 'category_type' )
    list_filter = ('group', 'parent', )
    search_fields = ('name',)

admin.site.register(models.Category, CategoryAdmin)

class CategoryLastVisitAdmin(admin.ModelAdmin):
    list_display = ('user', 'lastvisit')
    list_filter = ('user',)

admin.site.register(models.CategoryLastVisit, CategoryLastVisitAdmin)

admin.site.register(models.Post)


class MonitorAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'category', 'thread')
    list_filter = ('user', 'group')

admin.site.register(models.Monitor, MonitorAdmin)
admin.site.register(models.Poll)
admin.site.register(models.PollChoice)
admin.site.register(models.ExtendedCategoryConfig)

