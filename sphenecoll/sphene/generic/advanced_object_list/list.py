
from copy import deepcopy
import itertools

from django.template.loader import render_to_string
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe

from sphene.generic.advanced_object_list.columns import Column


__all__ = ('ObjectProvider', 'QuerySetProvider', 'AdvancedObjectList')


def get_declared_columns(bases, attrs, with_base_columns = True):
    columns = [(column_name, attrs.pop(column_name)) for column_name, obj in attrs.items() if isinstance(obj, Column)]
    columns.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))

    # TODO iterate over base classes

    return SortedDict(columns)


class DeclarativeColumnsMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['base_columns'] = get_declared_columns(bases, attrs)
        return type.__new__(cls, name, bases, attrs)

class ObjectProvider(object):
    def get_page(self, start, end):
        pass


class QuerySetProvider(object):
    def __init__(self, queryset, wrapper = None):
        self.queryset = queryset
        self.wrapper = wrapper

    def get_page(self, start, end):
        ret = self.queryset[start:end]
        if self.wrapper is not None:
            return itertools.imap(self.wrapper, ret)
        return ret


    def sort(self, column, sortorder):
        self.queryset = column.sort_queryset(self.queryset, sortorder)

class BaseAdvancedObjectList(object):
    def __init__(self, object_provider, template_name = 'sphene/community/generic/advanced_list.html',
                 state = None):
        self.columns = deepcopy(self.base_columns)
        self.object_provider = object_provider
        self.template_name = template_name
        self.state = state or { }

    def __unicode__(self):
        #return mark_safe(u'<table>%s%s</table>' % (self.render_header(),self.render_content(),))
        if 'sortby' in self.state:
            self.object_provider.sort(self.columns[self.state['sortby']], self.state['sortorder'])
        return render_to_string(self.template_name, { 'columns': self.columns.items(),
                                                      'content': self.get_content(),
                                                      'list': self, })

    def get_content(self):
        content = list()

        for object in self.object_provider.get_page(0, 20):
            columns = list()
            for column in self.columns.values():
                columns.append((column, column.get_value(object)),)
            content.append(columns)

        return content

    def render_header(self):
        ret = list()
        ret.append(u'<tr>')
        tmpl = u'<th>%(label)s</th>'
        for column in self.columns.values():
            ret.append(tmpl % { 'label': column.get_label() })
        ret.append(u'</tr>')
        return u''.join(ret)

    def render_content(self):
        ret = list()

        row_tmpl = u'<tr>%s</tr>'
        column_tmpl = u'<td>%s</td>'
        for object in self.object_provider.get_page(0, 20):
            cols = list()
            for column in self.columns.values():
                cols.append(column_tmpl % column.get_value(object))
            ret.append(row_tmpl % u''.join(cols))

        return u''.join(ret)

    def process_vars(self, request):
        pass

    def process_cmd(self, cmd):
        from django.conf import settings
        print "middleware: %s" % str(settings.MIDDLEWARE_CLASSES)
        bits = cmd.split('|')
        if bits[0] == 'sort':
            dir, column_name = bits[1:3]
            sortby = self.state.get('sortby', None)
            sortorder = self.state.get('sortorder', None)
            column = self.columns[column_name]
            if sortby != column_name:
                sortorder = None
                sortby = column_name
            if dir == 'toggle':
                default_sortorder = column.get_default_sortorder()
                if sortorder != default_sortorder:
                    sortorder = default_sortorder
                else:
                    if default_sortorder == 'asc':
                        sortorder = 'desc'
                    else:
                        sortorder = 'asc'

            self.state['sortby'] = sortby
            self.state['sortorder'] = sortorder

    def get_state(self):
        return self.state

class AdvancedObjectList(BaseAdvancedObjectList):
    __metaclass__ = DeclarativeColumnsMetaclass



