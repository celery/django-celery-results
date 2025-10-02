import json
import logging

from django.db import migrations, transaction

logger = logging.getLogger(__name__)


def safe_json_loads(value, default=None):
    """Safely parse JSON string with fallback."""
    if not value:  # Handles None, empty string, etc.
        return default
    return json.loads(value)


def make_copy_of_chordcounter_textfields(apps, schema_editor):
    chord_counter = apps.get_model('django_celery_results', 'ChordCounter')

    total_count = chord_counter.objects.count()
    logger.info(f"Starting migration for {total_count} ChordCounter records")

    batch_size = 500
    processed_count = 0
    error_count = 0
    last_id = 0

    while True:
        with transaction.atomic():
            # Get next batch using cursor pagination
            batch = list(
                chord_counter.objects.filter(id__gt=last_id)
                .order_by('id')[:batch_size]
            )

            if not batch:
                break

            updates = []

            for obj in batch:
                try:
                    # Parse JSON fields with appropriate defaults
                    obj.new_sub_tasks = safe_json_loads(obj.sub_tasks)
                    updates.append(obj)

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing ChordCounter ID {obj.id}: {e}")
                    continue

            if updates:
                chord_counter.objects.bulk_update(
                    updates,
                    ['new_sub_tasks']
                )
                processed_count += len(updates)

            last_id = batch[-1].id

            # Progress logging
            progress = (processed_count / total_count) * 100 if total_count > 0 else 0
            logger.info(f"Processed {processed_count}/{total_count} records ({progress:.1f}%)")

    logger.info(f"Migration completed. Successfully processed {processed_count} records, "
               f"{error_count} errors encountered")


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_results', '0016_make_copy_of_taskresult_textfields'),
    ]

    operations = [
        migrations.RunPython(
            make_copy_of_chordcounter_textfields,
            migrations.RunPython.noop
        )
    ]
