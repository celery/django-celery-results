Getting started
===============

To use :pypi:`django-celery-results` with your project you need to follow these steps:

#. Install the :pypi:`django-celery-results` library:

    .. code-block:: console

        $ pip install django-celery-results

#. Add ``django_celery_results`` to ``INSTALLED_APPS`` in your
   Django project's :file:`settings.py`::

        INSTALLED_APPS = (
            ...,
            'django_celery_results',
        )

   Note that there is no dash in the module name, only underscores.

#. Create the Celery database tables by performing a database migrations:

    .. code-block:: console

        $ python manage.py migrate django_celery_results

#. Configure Celery to use the :pypi:`django-celery-results` backend.

    Assuming you are using Django's :file:`settings.py` to also configure
    Celery, add the following settings:

    .. code-block:: python

        CELERY_RESULT_BACKEND = 'django-db'

    For the cache backend you can use:

    .. code-block:: python

        CELERY_CACHE_BACKEND = 'django-cache'

    We can also use the cache defined in the CACHES setting in django.

    .. code-block:: python

        # celery setting.
        CELERY_CACHE_BACKEND = 'default'

        # django setting.
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'my_cache_table',
            }
        }
        
    If you want to include extended information about your tasks remember to enable the `result_extended` setting. 
    More information here: https://docs.celeryq.dev/en/stable/userguide/configuration.html#result-extended
    
    .. code-block:: python
        
        CELERY_RESULT_EXTENDED = True

