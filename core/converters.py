from .utils import encode_id, decode_id

class HashidConverter:
    regex = '[a-zA-Z0-9_:-]+'

    def to_python(self, value):
        return decode_id(value)

    def to_url(self, value):
        return encode_id(value)
