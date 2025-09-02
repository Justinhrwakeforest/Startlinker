# Manual migration to fix company_email field nullability
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_alter_job_company_email'),
    ]

    operations = [
        # First, update existing empty values to empty strings
        migrations.RunSQL(
            "UPDATE jobs_job SET company_email = '' WHERE company_email IS NULL OR company_email = '';",
            reverse_sql="-- No reverse needed"
        ),
        # Then alter the field to be nullable but not null
        migrations.AlterField(
            model_name='job',
            name='company_email',
            field=models.EmailField(blank=True, default='', help_text='Company contact email (optional)', max_length=254),
        ),
    ]