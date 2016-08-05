"""Celery cache backend using the Django Cache Framework."""
from __future__ import absolute_import, unicode_literals

from django.core.cache import cache as default_cache, caches

from celery.backends.base import KeyValueStoreBackend


class CacheBackend(KeyValueStoreBackend):
    """Backend using the Django cache framework to store task metadata."""

    def get(self, key):
        return self.cache_backend.get(key)

    def set(self, key, value):
        self.cache_backend.set(key, value, self.expires)

    def delete(self, key):
        self.cache_backend.delete(key)

    @property
    def cache_backend(self):
        backend = self.app.conf.cache_backend
        return caches[backend] if backend else default_cache
