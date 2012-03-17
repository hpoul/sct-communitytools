
from django.conf import settings
from django.utils.translation import ugettext_lazy
from django.utils.html import escape
from django.utils.safestring import mark_safe

from sphene.generic import advanced_object_list as objlist


def makelink(object, column, value):
    return mark_safe('<a href="%s">%s</a>' % (object.get_absolute_url(),
                                              escape(value)))



class NewPostIndicator(objlist.Column):
    def _get_value(self, object):
        # {{ MEDIA_URL }}sphene/sphboard/icons/{% if thread.has_new_posts %}new{% endif %}folder.gif" width='16px' height='16px' title='Heat: {{ thread.heat }}' /></td
        return mark_safe( '<img src="%ssphene/sphboard/icons/%sfolder.gif" width="16px" height="16px" />' % (settings.MEDIA_URL, object.has_new_posts() and 'new' or '' ) )


class ThreadList(objlist.AdvancedObjectList):
    newpost = NewPostIndicator(
        label = '', )

    subject = objlist.AttributeColumn(
        'root_post.subject',
        label = ugettext_lazy( 'Subject' ),
        sortcolumn = 'root_post__subject',
        filter = makelink, )

    author = objlist.AttributeColumn(
        'root_post.author',
        label = ugettext_lazy( 'Author' ),
        sortcolumn = 'root_post__author',
        type = 'user', )

    views = objlist.AttributeColumn(
        'view_count',
        label = ugettext_lazy( 'Views' ),
        sortcolumn = 'view_count', )

    posts = objlist.AttributeColumn(
        'post_count',
        label = ugettext_lazy( 'Posts' ),
        sortcolumn = 'post_count', )

    latestpostdate = objlist.AttributeColumn(
        'latest_post.postdate',
        label = ugettext_lazy( 'Latest Post' ),
        sortcolumn = 'latest_post__postdate',
        type = 'date' )

    latestpostauthor = objlist.AttributeColumn(
        'latest_post.author',
        label = ugettext_lazy( 'Latest Post Author' ),
        sortcolumn = 'latest_post__author',
        type = 'user', )

    heat = objlist.AttributeColumn(
        'heat',
        label = ugettext_lazy( 'Heat' ),
        sortcolumn = 'heat', )




