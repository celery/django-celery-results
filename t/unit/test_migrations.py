import os

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings

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


class CompletionDateMigrationTests(TransactionTestCase):
    migrate_from = [
        ('django_celery_results', '0014_alter_taskresult_status'),
    ]
    migrate_to = [
        ('django_celery_results', '0015_taskresult_date_done_nullable'),
    ]

    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps.get_model(
            'django_celery_results', 'TaskResult')

    def setUp(self):
        super().setUp()
        self.addCleanup(self.migrate, self.migrate_to)
        self.old_model = self.migrate(self.migrate_from)

    def test_clear_unfinished_dates_and_preserve_completed_dates(self):
        completed = {}
        for state in ('SUCCESS', 'FAILURE', 'REVOKED'):
            result = self.old_model.objects.create(task_id=state, status=state)
            completed[state] = result.date_done

        unfinished = ('PENDING', 'STARTED', 'RETRY', 'PROGRESS')
        for state in unfinished:
            self.old_model.objects.create(task_id=state, status=state)

        TaskResult = self.migrate(self.migrate_to)

        for task_id, date_done in completed.items():
            self.assertEqual(
                TaskResult.objects.get(task_id=task_id).date_done, date_done)
        for task_id in unfinished:
            self.assertIsNone(
                TaskResult.objects.get(task_id=task_id).date_done)
        self.assertIsNone(
            TaskResult.objects.create(task_id='new-pending').date_done)

    def test_reverse_migration_fills_null_dates(self):
        TaskResult = self.migrate(self.migrate_to)
        unfinished = TaskResult.objects.create(task_id='unfinished')
        completed = TaskResult.objects.create(
            task_id='completed', status='SUCCESS',
            date_done=unfinished.date_created)

        TaskResult = self.migrate(self.migrate_from)

        self.assertEqual(
            TaskResult.objects.get(task_id='unfinished').date_done,
            unfinished.date_created)
        self.assertEqual(
            TaskResult.objects.get(task_id='completed').date_done,
            completed.date_done)
