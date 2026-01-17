"""
WSGI config for sims project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sims.settings')

application = get_wsgi_application()

