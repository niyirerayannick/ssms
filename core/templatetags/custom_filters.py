from django import template
import decimal

register = template.Library()

@register.filter
def compact_number(value):
    """
    Formats a large number into a compact string with suffixes (k, M, B).
    Examples:
        1,200 -> 1.2k
        1,500,000 -> 1.5M
        1,000,000,000 -> 1.0B
    """
    try:
        if value is None or value == '':
            return "0"
        
        value = float(value)
        
        if value < 1000:
            # For small numbers, just return as is (maybe with 2 decimal places if it has decimals)
            # Or integer if it's effectively an integer
            if value.is_integer():
                return f"{int(value)}"
            return f"{value:.2f}".rstrip('0').rstrip('.')
            
        if value >= 1_000_000_000:
            val = value / 1_000_000_000
            return f"{val:.1f}B".replace('.0B', 'B')
        elif value >= 1_000_000:
            val = value / 1_000_000
            return f"{val:.1f}M".replace('.0M', 'M')
        elif value >= 1_000:
            val = value / 1_000
            return f"{val:.1f}k".replace('.0k', 'k')
            
        return str(value)
    except (ValueError, TypeError):
        return value
