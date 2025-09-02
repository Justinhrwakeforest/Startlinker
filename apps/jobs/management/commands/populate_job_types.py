# apps/jobs/management/commands/populate_job_types.py

from django.core.management.base import BaseCommand
from apps.jobs.models import JobType

class Command(BaseCommand):
    help = 'Populate job types for production'

    def handle(self, *args, **options):
        job_types = [
            'Full-time',
            'Part-time', 
            'Contract',
            'Internship',
            'Freelance'
        ]
        
        created_count = 0
        for job_type_name in job_types:
            job_type, created = JobType.objects.get_or_create(name=job_type_name)
            if created:
                created_count += 1
                self.stdout.write(f"Created job type: {job_type_name}")
            else:
                self.stdout.write(f"Job type already exists: {job_type_name}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully populated {created_count} new job types')
        )