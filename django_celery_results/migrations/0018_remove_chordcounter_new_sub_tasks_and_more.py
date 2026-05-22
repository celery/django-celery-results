from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_results', '0017_make_copy_of_chordcounter_textfields'),
    ]

    operations = [
        # Remove the old fields
        migrations.RemoveField(
            model_name='chordcounter',
            name='sub_tasks',
        ),
        migrations.RemoveField(
            model_name='taskresult',
            name='meta',
        ),
        migrations.RemoveField(
            model_name='taskresult',
            name='task_args',
        ),
        migrations.RemoveField(
            model_name='taskresult',
            name='task_kwargs',
        ),

        # Rename the new_ fields to their non-prefixed versions
        migrations.RenameField(
            model_name='chordcounter',
            old_name='new_sub_tasks',
            new_name='sub_tasks',
        ),
        migrations.RenameField(
            model_name='taskresult',
            old_name='new_meta',
            new_name='meta',
        ),
        migrations.RenameField(
            model_name='taskresult',
            old_name='new_task_args',
            new_name='task_args',
        ),
        migrations.RenameField(
            model_name='taskresult',
            old_name='new_task_kwargs',
            new_name='task_kwargs',
        ),
    ]
