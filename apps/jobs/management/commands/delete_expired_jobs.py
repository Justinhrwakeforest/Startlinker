# startup_hub/apps/jobs/management/commands/delete_expired_jobs.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from apps.jobs.models import Job, JobBookmark
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Delete expired jobs and their associated bookmarks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (show what would be deleted without actually deleting)',
        )
        parser.add_argument(
            '--soft-delete',
            action='store_true',
            help='Soft delete jobs by setting status to "expired" instead of hard delete',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        soft_delete = options['soft_delete']
        
        self.stdout.write(self.style.SUCCESS('Starting expired jobs cleanup...'))
        
        # Find expired jobs
        now = timezone.now()
        expired_jobs = Job.objects.filter(
            expires_at__lt=now,
            status__in=['active', 'pending']  # Only delete active or pending jobs
        ).select_related('startup')
        
        total_expired = expired_jobs.count()
        
        if total_expired == 0:
            self.stdout.write(self.style.SUCCESS('No expired jobs found.'))
            return
        
        self.stdout.write(f'Found {total_expired} expired jobs')
        
        # Count bookmarks that will be affected
        job_ids = list(expired_jobs.values_list('id', flat=True))
        affected_bookmarks = JobBookmark.objects.filter(job_id__in=job_ids).count()
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write(f'Would delete {total_expired} expired jobs')
            self.stdout.write(f'Would remove {affected_bookmarks} associated bookmarks')
            
            # Show details of jobs that would be deleted
            for job in expired_jobs[:10]:  # Show first 10
                days_expired = (now - job.expires_at).days
                self.stdout.write(
                    f'  - {job.title} at {job.startup.name if job.startup else "Independent"} '
                    f'(expired {days_expired} days ago)'
                )
            
            if total_expired > 10:
                self.stdout.write(f'  ... and {total_expired - 10} more')
            
            return
        
        # Perform the deletion
        with transaction.atomic():
            if soft_delete:
                # Soft delete: change status to 'expired' and deactivate
                updated_count = expired_jobs.update(
                    status='expired',
                    is_active=False
                )
                
                # Remove bookmarks for expired jobs
                JobBookmark.objects.filter(job_id__in=job_ids).delete()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully marked {updated_count} jobs as expired and '
                        f'removed {affected_bookmarks} bookmarks'
                    )
                )
                logger.info(f'Soft deleted {updated_count} expired jobs and {affected_bookmarks} bookmarks')
                
            else:
                # Hard delete: completely remove jobs (bookmarks will be cascade deleted)
                deleted_jobs = []
                for job in expired_jobs:
                    deleted_jobs.append({
                        'id': job.id,
                        'title': job.title,
                        'startup': job.startup.name if job.startup else 'Independent',
                        'expired_days': (now - job.expires_at).days
                    })
                
                # Delete the jobs (this will cascade delete bookmarks due to FK constraints)
                deleted_count, deleted_objects = expired_jobs.delete()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully deleted {deleted_count} expired jobs and their bookmarks'
                    )
                )
                
                # Log deleted jobs
                for job_info in deleted_jobs:
                    logger.info(
                        f'Deleted expired job: {job_info["title"]} at {job_info["startup"]} '
                        f'(expired {job_info["expired_days"]} days ago)'
                    )
        
        self.stdout.write(self.style.SUCCESS('Expired jobs cleanup completed.'))