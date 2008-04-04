"""
just a few helper tags/filters for form rendering - DRY !!
"""


from django import template



register = template.Library()



@register.inclusion_tag('sphene/community/templatetags/_sph_form.html')
def sph_form(form):
    return { 'form': form, }
