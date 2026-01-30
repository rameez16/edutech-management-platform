from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get dictionary value by key
    Usage: {{ my_dict|get_item:my_key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """
    Multiply the value by the argument
    Usage: {{ value|multiply:10 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def percentage(value, total):
    """
    Calculate percentage
    Usage: {{ completed|percentage:total }}
    """
    try:
        if float(total) == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def status_color(status):
    """
    Return color based on status
    Usage: {{ status|status_color }}
    """
    colors = {
        'completed': 'var(--emerald-light)',
        'pending': 'var(--gold)',
        'delayed': 'var(--coral)',
        'planned': 'var(--cyan-light)',
        'evaluated': 'var(--emerald-light)',
        'submitted': 'var(--cyan-light)',
        'in_progress': 'var(--gold)',
        'not_started': 'var(--magenta-light)',
    }
    return colors.get(status, 'var(--cyan-light)')

@register.filter
def material_icon(material_type):
    """
    Return emoji icon for material type
    Usage: {{ material_type|material_icon }}
    """
    icons = {
        'recording': '📹',
        'notes': '📝',
        'slides': '📊',
        'code': '💻',
        'reference': '📚',
        'assignment': '📋',
        'other': '📄',
    }
    return icons.get(material_type, '📄')

@register.filter
def task_type_icon(task_type):
    """
    Return emoji icon for task type
    Usage: {{ task_type|task_type_icon }}
    """
    icons = {
        'homework': '📝',
        'assignment': '📋',
        'project': '🚀',
        'practice': '💪',
        'quiz': '❓',
    }
    return icons.get(task_type, '✏️')

@register.filter
def phase_badge_color(phase):
    """
    Return gradient for phase badge
    Usage: {{ phase|phase_badge_color }}
    """
    colors = {
        'phase1': 'linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(59, 130, 246, 0.3))',
        'phase2': 'linear-gradient(135deg, rgba(168, 85, 247, 0.3), rgba(217, 70, 239, 0.3))',
        'phase3': 'linear-gradient(135deg, rgba(249, 115, 22, 0.3), rgba(251, 146, 60, 0.3))',
    }
    return colors.get(phase, 'linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(168, 85, 247, 0.3))')