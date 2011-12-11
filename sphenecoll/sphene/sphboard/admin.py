from django.contrib import admin

from sphene.sphboard import models


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'parent', 'allowview', 'category_type', 'slug', )
    list_filter = ('group', 'parent',)
    prepopulated_fields = {"slug": ('name',)}
    search_fields = ('name','slug',)
admin.site.register(models.Category, CategoryAdmin)


class CategoryLastVisitAdmin(admin.ModelAdmin):
    list_display = ('user', 'lastvisit')
    list_filter = ('user',)
admin.site.register(models.CategoryLastVisit, CategoryLastVisitAdmin)


class MonitorAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'category', 'thread')
    list_filter = ('user', 'group')
admin.site.register(models.Monitor, MonitorAdmin)


admin.site.register(models.Post)
admin.site.register(models.Poll)
admin.site.register(models.PollChoice)
admin.site.register(models.ExtendedCategoryConfig)
admin.site.register(models.PostAttachment)
admin.site.register(models.PostAnnotation)
admin.site.register(models.ThreadInformation)
admin.site.register(models.ThreadLastVisit)
