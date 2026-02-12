from django.core.signing import Signer, BadSignature
from django.conf import settings

signer = Signer(sep=':', salt='id-encryption')

def encode_id(n):
    """Encodes an integer ID into an 'encrypted' string."""
    if n is None:
        return None
    return signer.sign(str(n))

def decode_id(e):
    """Decodes an 'encrypted' string back into an integer ID."""
    try:
        if not e:
            return None
        return int(signer.unsign(e))
    except (BadSignature, ValueError, TypeError):
        return None
