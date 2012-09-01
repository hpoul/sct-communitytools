from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

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


def user_email(obj):
    return obj.user.email
user_email.short_description = _('Email')

class MonitorAdmin(admin.ModelAdmin):
    list_display = ('user', user_email, 'group', 'category', 'thread')
    search_fields = ('user__username', 'user__email', 'category__name', 'thread__subject')
    raw_id_fields = ('user', 'group', 'category', 'thread')
admin.site.register(models.Monitor, MonitorAdmin)


admin.site.register(models.Post)
admin.site.register(models.Poll)
admin.site.register(models.PollChoice)
admin.site.register(models.ExtendedCategoryConfig)
admin.site.register(models.PostAttachment)
admin.site.register(models.PostAnnotation)
admin.site.register(models.ThreadInformation)
admin.site.register(models.ThreadLastVisit)
