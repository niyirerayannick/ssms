from django.core.signing import Signer, BadSignature
from django.conf import settings

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
