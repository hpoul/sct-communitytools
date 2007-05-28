from django import template

register = template.Library()

@register.inclusion_tag('sphene/community/_user_infos.html')
def showuserinfos():
    return { }
