# Post Ranking System

## Overview

This sophisticated post ranking system prioritizes content based on multiple factors to provide users with the most relevant and engaging posts. The system considers user relationships, engagement metrics, content quality, and temporal factors.

## Key Features

### 1. Personalized Ranking
- **Followed Users Boost**: Posts from users you follow receive significant priority
- **Interest-Based Filtering**: Algorithm learns from your interaction history
- **Topic Preferences**: Considers your engagement with different topics

### 2. Engagement Metrics
- **Likes**: Basic engagement signal (weight: 1.0)
- **Comments**: High-value engagement (weight: 3.0)
- **Shares**: Premium engagement signal (weight: 5.0)
- **Bookmarks**: Quality indicator (weight: 2.0)
- **Views**: Volume indicator (weight: 0.01)

### 3. Time Decay
- **Recency Boost**: Newer posts get higher scores
- **Half-life**: Post scores decay exponentially (24-hour half-life)
- **Trending Window**: Recent posts (48 hours) with high engagement get trending boost

### 4. Quality Indicators
- **Engagement Rate**: Likes and comments relative to views
- **Author Reputation**: Based on user's reputation score
- **Content Quality**: Determined by engagement patterns

## API Endpoints

### Ranked Feed
```
GET /api/posts/ranked_feed/
```

**Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Posts per page (default: 20)

**Response:**
```json
{
  "results": [...],
  "count": 20,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_previous": false,
  "algorithm_info": {
    "personalized": true,
    "factors": [
      "followed_users_boost",
      "engagement_metrics", 
      "time_decay",
      "quality_score",
      "author_reputation",
      "trending_score"
    ]
  }
}
```

### Smart Feed
```
GET /api/posts/smart_feed/
```

**Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Posts per page (default: 20)
- `boost_followed`: Boost posts from followed users (default: true)
- `topics`: Comma-separated topic slugs to include
- `exclude_seen`: Exclude previously viewed posts (default: false)

**Response:**
```json
{
  "results": [...],
  "count": 20,
  "user_interests": {
    "topics": {"tech": 15.5, "startup": 12.3},
    "authors": {1: 8.7, 2: 6.2}
  },
  "applied_filters": {
    "boost_followed": true,
    "include_topics": ["tech", "startup"],
    "exclude_seen": false
  }
}
```

## Ranking Algorithm

### Score Components

1. **Follow Boost**: `10.0` for posts from followed users
2. **Engagement Score**: Weighted sum of all interactions
3. **Recency Score**: Exponential decay based on post age
4. **Quality Score**: Engagement rate (interactions/views)
5. **Author Reputation**: Normalized reputation score (0-1)
6. **Trending Score**: Recent engagement velocity

### Final Score Formula
```
final_score = follow_boost + 
              (engagement_score * 1.0) + 
              (recency_score * 0.5) + 
              (quality_score * 0.3) + 
              (author_reputation * 0.2) + 
              (trending_score * 0.8)
```

## Performance Optimizations

### Caching Strategy
- **User-specific rankings**: Cached for 5 minutes
- **General rankings**: Cached for 10 minutes
- **Trending posts**: Cached for 30 minutes
- **User interests**: Cached for 6 hours

### Database Optimizations
- Pre-calculated ranking scores stored in `PostRankingScore` model
- Optimized queries with proper indexing
- Batch processing for score calculations

### Background Tasks
- Hourly ranking score updates via Celery
- Daily cleanup of old scores
- Real-time trending post updates

## User Interaction Tracking

The system tracks various user interactions to improve ranking:

- **View**: Post viewed (tracked with deduplication)
- **Like**: Post liked/reacted to
- **Comment**: User commented on post
- **Share**: Post shared on external platforms
- **Bookmark**: Post bookmarked for later
- **Click Profile**: User clicked on author profile
- **Click Link**: User clicked on external links
- **Time Spent**: Reading time tracking (if implemented)

## Management Commands

### Calculate Ranking Scores
```bash
python manage.py calculate_ranking_scores
```

**Options:**
- `--batch-size`: Number of posts per batch (default: 1000)
- `--force`: Recalculate all scores regardless of age
- `--recent-only`: Only process posts from last 7 days
- `--verbose`: Enable detailed output

### Example Usage
```bash
# Calculate scores for all posts
python manage.py calculate_ranking_scores

# Process only recent posts with verbose output
python manage.py calculate_ranking_scores --recent-only --verbose

# Force recalculation of all scores
python manage.py calculate_ranking_scores --force --batch-size 500
```

## Celery Tasks

### Periodic Tasks (recommended schedule)
```python
# settings.py
CELERY_BEAT_SCHEDULE = {
    'calculate-ranking-scores': {
        'task': 'apps.posts.tasks.calculate_ranking_scores_task',
        'schedule': crontab(minute=0),  # Every hour
        'kwargs': {'recent_only': True}
    },
    'cleanup-old-scores': {
        'task': 'apps.posts.tasks.cleanup_old_ranking_scores',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'update-trending': {
        'task': 'apps.posts.tasks.update_trending_posts',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}
```

## Monitoring and Analytics

### Key Metrics to Track
- Ranking score distribution
- Cache hit rates
- Algorithm performance
- User engagement with ranked content
- Click-through rates from feed

### Logging
The system logs important events:
- Ranking calculations
- Cache operations
- Error conditions
- Performance metrics

## Future Enhancements

### Planned Features
1. **Machine Learning Integration**: Use ML models for more sophisticated ranking
2. **A/B Testing Framework**: Test different ranking algorithms
3. **Real-time Updates**: WebSocket-based real-time ranking updates
4. **Advanced Personalization**: More granular user preference learning
5. **Content Similarity**: Factor in content similarity for recommendations

### Potential Optimizations
1. **Elasticsearch Integration**: For faster full-text search and ranking
2. **Redis Clustering**: For better cache performance
3. **GraphQL Support**: More efficient data fetching
4. **Mobile-specific Ranking**: Different algorithms for mobile users

## Contributing

When making changes to the ranking system:

1. Update tests for any algorithm changes
2. Monitor performance impact in production
3. Document any new ranking factors
4. Consider backward compatibility
5. Update this documentation

## Troubleshooting

### Common Issues

**Slow ranking queries**
- Check database indexes
- Verify cache configuration
- Monitor query execution plans

**Inconsistent rankings**
- Ensure ranking scores are up to date
- Check for clock synchronization issues
- Verify cache invalidation

**Missing personalization**
- Confirm user authentication
- Check follow relationships
- Verify interaction tracking

### Debug Commands
```bash
# Check ranking scores
python manage.py shell -c "from apps.posts.models import PostRankingScore; print(PostRankingScore.objects.count())"

# Test ranking service
python manage.py shell -c "from apps.posts.ranking import PostRankingService; rs = PostRankingService(); print(len(rs.get_ranked_posts(10)))"

# Clear ranking caches
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```