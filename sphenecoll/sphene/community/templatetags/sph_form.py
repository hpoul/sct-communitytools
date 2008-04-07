"""
just a few helper tags/filters for form rendering - DRY !!
"""


from django import template
from django.utils.translation import ugettext


register = template.Library()



@register.inclusion_tag('sphene/community/templatetags/_sph_form.html')
def sph_form(form, submitlabel = ugettext('Save')):
    return { 'form': form,
             'submitlabel': submitlabel, }
