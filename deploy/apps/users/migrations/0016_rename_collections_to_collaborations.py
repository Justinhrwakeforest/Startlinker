# Generated migration to rename collections to collaborations

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_add_collaboration_features'),
    ]

    operations = [
        # Add metadata field to StartupCollection before renaming
        migrations.AddField(
            model_name='startupcollection',
            name='metadata',
            field=models.JSONField(blank=True, default=dict, help_text='Extended metadata for the collaboration including resources, tools, progress tracking, etc.'),
        ),
    ]