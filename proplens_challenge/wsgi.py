"""
WSGI config for proplens_challenge project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proplens_challenge.settings')

application = get_wsgi_application()

