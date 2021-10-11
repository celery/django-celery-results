import os

from django.core.management import call_command
from django.test import TestCase, override_settings

from django_celery_results import migrations as result_migrations


class MigrationTests(TestCase):
    def test_no_duplicate_migration_numbers(self):
        """Verify no duplicate migration numbers.

        Migration files with the same number can cause issues with
        backward migrations, so avoid them.
        """
        path = os.path.dirname(result_migrations.__file__)
        files = [f[:4] for f in os.listdir(path) if f.endswith('.py')]
        self.assertEqual(
            len(files), len(set(files)),
            msg='Detected migration files with the same migration number')

    def test_models_match_migrations(self):
        """Make sure that no pending migrations exist for the app.

        Here just detect if model changes exist that require
        a migration, and if so we fail.
        """
        call_command(
            "makemigrations", "django_celery_results", "--check", "--dry-run"
        )

    @override_settings(DEFAULT_AUTO_FIELD='django.db.models.BigAutoField')
    def test_models_match_migrations_with_changed_default_auto_field(self):
        """Test with changing default_auto_field.

        This logic make sure that no pending migrations created even if
        the user changes the `DEFAULT_AUTO_FIELD`.
        """
        self.test_models_match_migrations()
