from __future__ import absolute_import, unicode_literals
from django.conf import settings

if settings.CELERY_RESULT_BACKEND == 'django-cache':
    from .cache import CacheBackend
else:
    from .database import DatabaseBackend

__all__ = ['CacheBackend', 'DatabaseBackend']
