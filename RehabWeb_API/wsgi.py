"""
WSGI config for RehabWeb_API project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RehabWeb_API.settings')

application = get_wsgi_application()
