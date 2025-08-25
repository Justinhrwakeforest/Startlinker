# startup_hub/apps/posts/management/commands/calculate_ranking_scores.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from apps.posts.ranking import PostRankingService
from apps.posts.models import Post, PostRankingScore
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculate and update ranking scores for all posts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of posts to process in each batch (default: 1000)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recalculation of all scores, even recent ones'
        )
        
        parser.add_argument(
            '--recent-only',
            action='store_true',
            help='Only calculate scores for posts from the last 7 days'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
    
    def handle(self, *args, **options):
        batch_size = options['batch_size']
        force = options['force']
        recent_only = options['recent_only']
        verbose = options['verbose']
        
        if verbose:
            logger.setLevel(logging.INFO)
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting ranking score calculation...')
        )
        
        try:
            # Initialize ranking service
            ranking_service = PostRankingService()
            
            # Get posts to process
            posts_queryset = Post.objects.filter(
                is_approved=True,
                is_draft=False
            ).select_related('author__connect_profile')
            
            if recent_only:
                cutoff_date = timezone.now() - timezone.timedelta(days=7)
                posts_queryset = posts_queryset.filter(created_at__gte=cutoff_date)
                self.stdout.write(f'Processing posts from the last 7 days only')
            
            if not force:
                # Only process posts that haven't been calculated in the last hour
                cutoff_time = timezone.now() - timezone.timedelta(hours=1)
                # Get posts that either don't have a ranking score or have an old one
                posts_without_recent_scores = posts_queryset.filter(
                    models.Q(ranking_score__isnull=True) |
                    models.Q(ranking_score__calculated_at__lt=cutoff_time)
                )
                posts_queryset = posts_without_recent_scores
                self.stdout.write(f'Skipping posts with recent scores (calculated within 1 hour)')
            
            total_posts = posts_queryset.count()
            
            if total_posts == 0:
                self.stdout.write(
                    self.style.WARNING('No posts to process.')
                )
                return
            
            self.stdout.write(f'Processing {total_posts} posts in batches of {batch_size}')
            
            processed = 0
            errors = 0
            
            # Process in batches
            for i in range(0, total_posts, batch_size):
                batch = posts_queryset[i:i + batch_size]
                
                try:
                    batch_scores = ranking_service._calculate_batch_scores(batch)
                    processed += len(batch_scores)
                    
                    if verbose:
                        self.stdout.write(f'Processed batch {i//batch_size + 1}: {len(batch_scores)} posts')
                    
                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'Error processing batch {i//batch_size + 1}: {e}')
                    )
                
                # Progress update
                if (i + batch_size) % (batch_size * 5) == 0 or i + batch_size >= total_posts:
                    percentage = min(100, ((i + batch_size) / total_posts) * 100)
                    self.stdout.write(f'Progress: {percentage:.1f}% ({min(i + batch_size, total_posts)}/{total_posts})')
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'Ranking score calculation completed!\n'
                    f'Processed: {processed} posts\n'
                    f'Errors: {errors} batches\n'
                    f'Total ranking scores in database: {PostRankingScore.objects.count()}'
                )
            )
            
            # Clean up old ranking scores (optional)
            if options.get('cleanup', False):
                self._cleanup_old_scores()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Fatal error during ranking calculation: {e}')
            )
            logger.error(f'Fatal error in calculate_ranking_scores command: {e}')
            raise
    
    def _cleanup_old_scores(self):
        """Remove ranking scores for posts that no longer exist"""
        try:
            # Find ranking scores for posts that have been deleted
            orphaned_scores = PostRankingScore.objects.filter(
                post__isnull=True
            )
            count = orphaned_scores.count()
            
            if count > 0:
                orphaned_scores.delete()
                self.stdout.write(f'Cleaned up {count} orphaned ranking scores')
            else:
                self.stdout.write('No orphaned ranking scores found')
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Error during cleanup: {e}')
            )