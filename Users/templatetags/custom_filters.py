from django import template
import datetime

register = template.Library()

@register.filter(name='japanese_date')
def japanese_date(value):
    if isinstance(value, datetime.date):
        return value.strftime('%Y年%m月%d日')
    return value

@register.filter(name='dict_key')
def dict_key(d, key):
    return d.get(key)