from django.core.signing import Signer, BadSignature
from django.conf import settings
from decimal import Decimal, InvalidOperation

signer = Signer(sep=':', salt='id-encryption')

def encode_id(n):
    """Encodes an integer ID into an 'encrypted' string."""
    if n is None:
        return None
    return signer.sign(str(n))

def decode_id(e):
    """Decodes an 'encrypted' string back into an integer ID.
    Falls back to parsing as integer if not a signed string.
    """
    if not e:
        return None
    
    try:
        # Try to unsign it first
        return int(signer.unsign(str(e)))
    except (BadSignature, ValueError, TypeError):
        # Fallback to plain integer if it's already an ID or numeric string
        try:
            return int(e)
        except (ValueError, TypeError):
            return None


def normalize_identifier_value(value, empty_value=''):
    """Normalize phone/account identifiers so numeric imports do not show trailing decimals."""
    if value is None:
        return empty_value

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else format(value, 'f').rstrip('0').rstrip('.')

    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return str(value.quantize(Decimal('1')))
        return format(value.normalize(), 'f').rstrip('0').rstrip('.')

    text = str(value).strip()
    if not text:
        return empty_value

    if text.endswith('.0'):
        candidate = text[:-2]
        if candidate.replace('+', '', 1).isdigit():
            return candidate
        try:
            parsed = Decimal(text)
            if parsed == parsed.to_integral_value():
                return str(parsed.quantize(Decimal('1')))
        except (InvalidOperation, ValueError):
            pass

    return text
