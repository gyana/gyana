ICONS = {
    "success": "fa-check-circle text-green",
    "error": "fa-times-hexagon text-red",
    "warning": "fa-exclamation-triangle text-orange",
}


icon_html = """
<div class='tooltip tooltip--bottom text-center'>
    <i class='fa {icon}'></i>
    <span class='tooltip__content'>{text}</span>
</div>
"""
