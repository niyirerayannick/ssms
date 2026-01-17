"""
ASGI config for sims project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')

application = get_asgi_application()

