from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter(name='field_from_name')
def field_from_name(form, field_name):
    try:
        return form[field_name]
    except:
        return None

@register.filter(name='first_field_name')
def first_field_name(form):
    if form and hasattr(form, 'fields') and form.fields:
        return list(form.fields.keys())[0] if form.fields else ''
    return ''