
from copy import deepcopy
import itertools

from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy

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

    def total_count(self):
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

    def total_count(self):
        if isinstance(self.queryset, list):
            return len(self.queryset)
        return self.queryset.count()

class MultiColumn(Column):
    def __init__(self, subcolumns, *args, **kwargs):
        super(MultiColumn, self).__init__(*args, **kwargs)
        self.subcolumns = subcolumns

    def is_multicolumn(self):
        return True

    def _get_value(self, object):
        #    columns = list()
        #    for column in self.columns.values():
        #        columns.append((column, column.get_value(object)),)
        #    content.append(columns)
        return [ (c, c.get_value(object)) for cid,c in self.subcolumns ]

class BaseAdvancedObjectList(object):
    def __init__(self, object_provider, template_name = 'sphene/community/generic/advanced_list.html',
                 state = None, object_name = ugettext_lazy('Items'),
                 prefix = 'objlist', session = None, requestvars = None, defaultcolconfig = None, defaultsortby = None, defaultsortorder = None, cssclass = None):
        self._prepared = False
        #self.columns = deepcopy(self.base_columns)
        self.object_provider = object_provider
        self.template_name = template_name
        self.object_name = object_name
        self.prefix = prefix
        self.cssclass = cssclass or prefix
        self.defaultcolconfig = defaultcolconfig
        self.defaultsortby = defaultsortby
        self.defaultsortorder = defaultsortorder
        self.pagesize = 10
        if state is None and session is not None:
            self.state = session.get(prefix, {})
        else:
            self.state = state or { }
        if requestvars is not None:
            self.process_vars(requestvars)
            if session is not None:
                session[prefix] = self.state


    def prepare_column_config(self, colconfig, is_subcol = False):
        instance_columns = list()
        i=0
        for colc in colconfig:
            colid = colc
            if isinstance(colc, dict):
                column_name = colc['column']
                column = self.base_columns[column_name]
                column = column.new_configure(colc)
                colid = "%s.%d" % (column_name, i)
            elif isinstance(colc, tuple) or isinstance(colc, list):
                colid = "multicol.%d" % i
                column = self.prepare_column_config(colc, True)
                instance_columns.append(column)
                continue
            else:
                colid = colc
                column = self.base_columns[colc]

            # list in list in list ;)
            if not is_subcol:
                instance_columns.append(((colid, column,),),)
            else:
                instance_columns.append((colid, column,),)
            self.allcolumns[colid] = column
            i+=1

        return instance_columns


    def prepare(self):
        """
        configures all columns based on the list's state
        """
        if self._prepared:
            return
        
        colconfig = self.state.get('colconfig', self.defaultcolconfig)
        self.colconfig = colconfig
        self.allcolumns = {}

        instance_columns = self.prepare_column_config(colconfig)

        self.columns = instance_columns #SortedDict(instance_columns)
        self._prepared = True

    def get_sorting(self):
        return self.state.get('sortby', self.defaultsortby), \
            self.state.get('sortorder', self.defaultsortorder)

    def get_paging(self):
        """
        returns a dict of:
        1. pagesize
        2. current page
        3. first item
        4. last item of current page (no check is made if there are actualy
           so many items!!)
        """
        page = self.state.get('page', 1)
        pagesize = self.pagesize
        return { 'pagesize': pagesize, 
                 'page': page,
                 'first': (page-1) * pagesize,
                 'last': page * pagesize, }

    def get_object_count(self):
        if hasattr(self, '_object_count'):
            return self._object_count
        self._object_count = self.object_provider.total_count()
        return self._object_count

    def __unicode__(self):
        if not self._prepared:
            self.prepare()

        #return mark_safe(u'<table>%s%s</table>' % (self.render_header(),self.render_content(),))
        sortby, sortorder = self.get_sorting()
        if sortby is not None:
            try:
                self.object_provider.sort(self.allcolumns[sortby], sortorder)
            except KeyError:
                pass
        object_count = self.get_object_count()#self.object_provider.total_count()
        paging = self.get_paging()
        paging['hasnext'] = object_count > paging['last']
        paging['hasprev'] = paging['page'] > 0
        paging['pages'] = object_count // paging['pagesize'] + 1
        paging['getparam'] = '%s.page' % self.prefix
        return render_to_string(self.template_name, { 'columns': self.columns,
                                                      'content': self.get_content(),
                                                      'list': self,
                                                      'object_name': self.object_name,
                                                      'object_count': object_count,
                                                      'paging': paging, })

    def get_content(self):
        content = list()

        paging = self.get_paging()
        for object in self.object_provider.get_page(paging['first'],paging['last']):
            columns = list()
            for subcolumns in self.columns:
                columns.append( [ (cid, column, column.get_value(object)) \
                                      for cid, column in subcolumns ] )
                #columns.append((column, column.get_value(object)),)
            content.append(columns)

        return content

    """
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
    """

    def process_vars(self, requestvars):
        self.state['page'] = int(requestvars.get("%s.page" % self.prefix, 1))
        try:
            self.process_cmd(requestvars["%s.cmd" % self.prefix], requestvars)
        except KeyError, e:
            return

    def colconfig_json(self):
        return simplejson.dumps(self.colconfig)

    def is_customized(self):
        return 'colconfig' in self.state

    def process_cmd(self, cmd, requestvars = {}):
        if cmd == 'colconfig':
            colconfig = requestvars["%s.colconfig" % self.prefix]
            colconfig = simplejson.loads(colconfig)
            self.state['colconfig'] = colconfig
            return
        elif cmd == 'revert':
            del self.state['colconfig']
            return
        self.prepare()
        from django.conf import settings
        bits = cmd.split('|')
        if bits[0] == 'sort':
            dir, column_name = bits[1:3]
            sortby, sortorder = self.get_sorting()
            #sortby = self.state.get('sortby', None)
            #sortorder = self.state.get('sortorder', None)
            column = self.allcolumns[column_name]
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


class AdvancedObjectList(BaseAdvancedObjectList):
    __metaclass__ = DeclarativeColumnsMetaclass



