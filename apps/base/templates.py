from django import template


def template_exists(template_name):
    try:
        template.loader.get_template(template_name)
        return True
    except template.TemplateDoesNotExist:
        return False
