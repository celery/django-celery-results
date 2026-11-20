"""Application settings."""
from dataclasses import dataclass
from typing import Any

from django.conf import settings as django_settings

# All attributes accessed with this prefix are possible
# to overwrite through django.conf.settings.
SETTINGS_PREFIX = "DJANGO_CELERY_RESULTS_"


@dataclass(frozen=True)
class AppSettings:
    """Proxy class to encapsulate all the app settings.

    This instance should be accessed via the singleton
    ``django_celery_results.conf.app_settings``.

    You shouldn't have to set any of these yourself, the class checks a Django
    settings with the same name and use these if defined, defaulting to the
    values documented here.
    """

    DJANGO_CELERY_RESULTS_TASK_ID_MAX_LENGTH: int = 255

    def __getattribute__(self, __name: str) -> Any:
        """Check if a Django project settings should override the app default.

        In order to avoid returning any random properties of the Django
        settings, we first inspect the prefix.
        """
        if (
            __name.startswith(SETTINGS_PREFIX)
            and hasattr(django_settings, __name)
        ):
            return getattr(django_settings, __name)

        return super().__getattribute__(__name)


app_settings = AppSettings()
