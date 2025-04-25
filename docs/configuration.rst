Configuration
=============

These are the available settings that can be configured in your Django
project's settings module by defining a setting with the same name.

* ``DJANGO_CELERY_RESULTS_DEFAULT_AUTO_FIELD``: The ``default_auto_field`` used
  when first deploying the app, defaults to ``django.db.models.BigAutoField``
  if unspecified.

  This is only used for the first deployment and
  and has no effect if changed after this point. If you want to change its
  value after the initial deployment, you should migrate back to zero and
  re-apply migrations again::

    $ python manage.py migrate django_celery_results zero
    $ python manage.py migrate django_celery_results

  This will drop and recreate all tables used by django-celery-results.
