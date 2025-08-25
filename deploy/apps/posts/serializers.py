# startup_hub/apps/posts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Exists, OuterRef, F
from .models import (
    Topic, Post, PostImage, PostLink, Comment, PostReaction,
    CommentReaction, PostBookmark, PostView, PostShare, Mention,
    PostReport, Poll, PollOption, PollVote
)
import re
from django.db import transaction
from django.utils.timesince import timesince

User = get_user_model()

class TopicSerializer(serializers.ModelSerializer):
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = ['id', 'name', 'slug', 'description', 'icon', 'post_count', 'follower_count', 'is_following']
        read_only_fields = ['slug', 'post_count', 'follower_count']
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Would need TopicFollow model
            return False
        return False

class PostImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'caption', 'order']
    
    def get_image(self, obj):
        """Return full URL for the image"""
        if obj.image:
            from django.conf import settings
            if obj.image.url.startswith('http'):
                return obj.image.url
            else:
                # Build full URL with backend domain
                backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000')
                return f"{backend_url}{obj.image.url}"
        return None

class PostLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLink
        fields = ['id', 'url', 'title', 'description', 'image_url', 'domain']
        read_only_fields = ['title', 'description', 'image_url', 'domain']

class AuthorSerializer(serializers.ModelSerializer):
    """Enhanced serializer for post/comment authors"""
    full_name = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    headline = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'display_name', 
            'avatar_url', 'is_verified', 'is_online', 'headline',
            'is_following'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_display_name(self, obj):
        # Priority: Full name > Username
        full_name = obj.get_full_name()
        return full_name if full_name else obj.username
    
    def get_avatar_url(self, obj):
        # Use the User model's get_avatar_url method
        return obj.get_avatar_url()
    
    def get_is_verified(self, obj):
        return obj.is_staff or getattr(obj, 'is_verified', False)
    
    def get_is_online(self, obj):
        if hasattr(obj, 'connect_profile') and obj.connect_profile.show_online_status:
            return obj.connect_profile.is_online
        return False
    
    def get_headline(self, obj):
        if hasattr(obj, 'connect_profile'):
            return obj.connect_profile.headline
        return ""
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user != obj:
            from apps.connect.models import Follow
            return Follow.objects.filter(
                follower=request.user,
                following=obj
            ).exists()
        return False

class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    author_name = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    time_since = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'author', 'author_name', 'parent', 'content',
            'is_anonymous', 'created_at', 'updated_at', 'edited_at',
            'like_count', 'reply_count', 'replies', 'is_liked',
            'can_edit', 'can_delete', 'time_since'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at', 'edited_at', 'like_count', 'reply_count']
    
    def get_author_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return obj.author.get_full_name() or obj.author.username
    
    def get_replies(self, obj):
        if obj.parent is None:  # Only show replies for top-level comments
            replies = obj.replies.all().order_by('created_at')[:5]  # Limit to 5 replies
            return CommentSerializer(replies, many=True, context=self.context).data
        return []
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reactions.filter(user=request.user).exists()
        return False
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_edit(request.user)
        return False
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user == obj.author or request.user.is_staff
        return False
    
    def get_time_since(self, obj):
        return timesince(obj.created_at)

class PostReactionSerializer(serializers.ModelSerializer):
    user = AuthorSerializer(read_only=True)
    
    class Meta:
        model = PostReaction
        fields = ['id', 'user', 'reaction_type', 'created_at']
        read_only_fields = ['user', 'created_at']

class PollOptionSerializer(serializers.ModelSerializer):
    percentage = serializers.SerializerMethodField()
    is_voted = serializers.SerializerMethodField()
    
    class Meta:
        model = PollOption
        fields = ['id', 'text', 'vote_count', 'percentage', 'is_voted', 'order']
        read_only_fields = ['vote_count', 'percentage', 'is_voted']
    
    def get_percentage(self, obj):
        return obj.get_percentage()
    
    def get_is_voted(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.votes.filter(user=request.user).exists()
        return False

class PollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True, read_only=True)
    user_has_voted = serializers.SerializerMethodField()
    user_votes = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Poll
        fields = [
            'id', 'multiple_choice', 'max_selections', 'anonymous_voting',
            'show_results_before_vote', 'allow_result_view_without_vote',
            'ends_at', 'total_votes', 'options', 'user_has_voted', 'user_votes',
            'is_active', 'time_remaining'
        ]
        read_only_fields = ['total_votes', 'user_has_voted', 'user_votes', 'is_active', 'time_remaining']
    
    def get_user_has_voted(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.user_has_voted(request.user)
        return False
    
    def get_user_votes(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return list(obj.get_user_votes(request.user))
        return []
    
    def get_is_active(self, obj):
        return obj.is_active()
    
    def get_time_remaining(self, obj):
        if not obj.ends_at:
            return None
        if obj.is_active():
            return int((obj.ends_at - timezone.now()).total_seconds())
        return 0

class PollVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollVote
        fields = ['option']
        
    def validate(self, data):
        poll = self.context['poll']
        user = self.context['request'].user
        option = data['option']
        
        # Check if poll is active
        if not poll.is_active():
            raise serializers.ValidationError("This poll has ended.")
        
        # Check if option belongs to this poll
        if option.poll != poll:
            raise serializers.ValidationError("Invalid poll option.")
        
        # Check if user already voted (for single choice polls)
        if not poll.multiple_choice and poll.user_has_voted(user):
            raise serializers.ValidationError("You have already voted in this poll.")
        
        # Check if user already voted for this specific option
        if poll.votes.filter(user=user, option=option).exists():
            raise serializers.ValidationError("You have already voted for this option.")
        
        # Check max selections for multiple choice polls
        if poll.multiple_choice:
            user_vote_count = poll.votes.filter(user=user).count()
            if user_vote_count >= poll.max_selections:
                raise serializers.ValidationError(f"You can only vote for up to {poll.max_selections} options.")
        
        return data

class PostListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    author_name = serializers.SerializerMethodField()
    topics = TopicSerializer(many=True, read_only=True)
    topic_names = serializers.ListField(write_only=True, required=False)
    
    # Metrics
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    
    # Permissions
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    # Related content preview
    first_image = serializers.SerializerMethodField()
    content_preview = serializers.SerializerMethodField()
    time_since = serializers.SerializerMethodField()
    read_time = serializers.SerializerMethodField()
    
    # Engagement
    has_user_interacted = serializers.SerializerMethodField()
    top_reactions = serializers.SerializerMethodField()
    
    # Poll
    poll = PollSerializer(read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'author', 'author_name', 'title', 'content_preview', 'post_type',
            'topics', 'topic_names', 'is_anonymous', 'is_pinned', 'is_locked',
            'created_at', 'updated_at', 'view_count', 'like_count', 'comment_count',
            'share_count', 'bookmark_count', 'is_liked', 'is_bookmarked',
            'user_reaction', 'can_edit', 'can_delete', 'first_image',
            'time_since', 'read_time', 'has_user_interacted', 'top_reactions', 'poll'
        ]
        read_only_fields = [
            'author', 'created_at', 'updated_at', 'view_count', 'like_count',
            'comment_count', 'share_count', 'bookmark_count'
        ]
    
    def get_author_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return obj.author.get_full_name() or obj.author.username
    
    def get_content_preview(self, obj):
        # Strip HTML tags if any
        import re
        clean_content = re.sub('<.*?>', '', obj.content)
        # Return first 200 characters
        return clean_content[:200] + '...' if len(clean_content) > 200 else clean_content
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reactions.filter(user=request.user).exists()
        return False
    
    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.bookmarks.filter(user=request.user).exists()
        return False
    
    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            reaction = obj.reactions.filter(user=request.user).first()
            if reaction:
                return {
                    'type': reaction.reaction_type,
                    'emoji': dict(PostReaction.REACTION_TYPES).get(reaction.reaction_type)
                }
        return None
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_edit(request.user)
        return False
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_delete(request.user)
        return False
    
    def get_first_image(self, obj):
        first_image = obj.images.first()
        if first_image:
            return PostImageSerializer(first_image).data
        return None
    
    def get_time_since(self, obj):
        return timesince(obj.created_at)
    
    def get_read_time(self, obj):
        # Estimate read time based on word count
        word_count = len(obj.content.split())
        minutes = max(1, word_count // 200)  # Average reading speed
        return f"{minutes} min read"
    
    def get_has_user_interacted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return any([
                self.get_is_liked(obj),
                self.get_is_bookmarked(obj),
                obj.comments.filter(author=request.user).exists()
            ])
        return False
    
    def get_top_reactions(self, obj):
        # Get top 3 reaction types
        reactions = obj.reactions.values('reaction_type').annotate(
            count=Count('id')
        ).order_by('-count')[:3]
        
        return [
            {
                'type': r['reaction_type'],
                'emoji': dict(PostReaction.REACTION_TYPES).get(r['reaction_type']),
                'count': r['count']
            }
            for r in reactions
        ]

class PostDetailSerializer(PostListSerializer):
    """Detailed post serializer with all content"""
    content = serializers.CharField()  # Full content
    images = PostImageSerializer(many=True, read_only=True)
    links = PostLinkSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    reactions_summary = serializers.SerializerMethodField()
    related_startup = serializers.SerializerMethodField()
    related_job = serializers.SerializerMethodField()
    mentioned_users = serializers.SerializerMethodField()
    viewer_has_viewed = serializers.SerializerMethodField()
    
    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + [
            'content', 'images', 'links', 'comments', 'comments_count',
            'reactions_summary', 'related_startup', 'related_job', 
            'slug', 'meta_description', 'mentioned_users', 'viewer_has_viewed',
            'edited_at', 'edit_count'
        ]
    
    def get_comments(self, obj):
        # Get top-level comments only, sorted by engagement
        comments = obj.comments.filter(
            parent=None
        ).annotate(
            engagement=Count('reactions') + Count('replies')
        ).order_by('-engagement', '-created_at')[:20]
        
        return CommentSerializer(comments, many=True, context=self.context).data
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_reactions_summary(self, obj):
        # Group reactions by type with user preview
        summary = {}
        for reaction_type, emoji in PostReaction.REACTION_TYPES:
            reactions = obj.reactions.filter(reaction_type=reaction_type).select_related('user')
            count = reactions.count()
            if count > 0:
                summary[reaction_type] = {
                    'emoji': emoji,
                    'count': count,
                    'users': AuthorSerializer(
                        [r.user for r in reactions[:3]], 
                        many=True, 
                        context=self.context
                    ).data,
                    'has_more': count > 3
                }
        return summary
    
    def get_related_startup(self, obj):
        if obj.related_startup:
            from apps.startups.serializers import StartupListSerializer
            return StartupListSerializer(obj.related_startup, context=self.context).data
        return None
    
    def get_related_job(self, obj):
        if obj.related_job:
            from apps.jobs.serializers import JobListSerializer
            return JobListSerializer(obj.related_job, context=self.context).data
        return None
    
    def get_mentioned_users(self, obj):
        mentions = Mention.objects.filter(post=obj).select_related('mentioned_user')
        return AuthorSerializer(
            [m.mentioned_user for m in mentions], 
            many=True, 
            context=self.context
        ).data
    
    def get_viewer_has_viewed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.views.filter(user=request.user).exists()
        return False

class PostCreateSerializer(serializers.ModelSerializer):
    """Enhanced serializer for creating posts"""
    topic_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        max_length=10  # Max 10 images
    )
    mentioned_users = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    poll_options = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False,
        min_length=2,
        max_length=5
    )
    
    class Meta:
        model = Post
        fields = [
            'title', 'content', 'post_type', 'is_anonymous', 'is_draft',
            'topic_names', 'images', 'mentioned_users', 'related_startup',
            'related_job', 'poll_options'
        ]
    
    def validate_content(self, value):
        print(f"🔍 Validating content: '{value}' (length: {len(value)})")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Content must be at least 10 characters long.")
        if len(value) > 10000:
            raise serializers.ValidationError("Content must be less than 10,000 characters.")
        return value
    
    def validate_title(self, value):
        if value and len(value) > 200:
            raise serializers.ValidationError("Title must be less than 200 characters.")
        return value
    
    def create(self, validated_data):
        print(f"🔍 Creating post with data: {validated_data}")
        topic_names = validated_data.pop('topic_names', [])
        images = validated_data.pop('images', [])
        mentioned_users = validated_data.pop('mentioned_users', [])
        poll_options = validated_data.pop('poll_options', [])
        
        print(f"🔍 Topic names: {topic_names}")
        print(f"🔍 Images count: {len(images)}")
        print(f"🔍 Poll options: {poll_options}")
        
        with transaction.atomic():
            # Create post
            post = Post.objects.create(**validated_data)
            
            # Handle topics
            for topic_name in topic_names:
                topic_name = topic_name.strip().lower()
                if topic_name and topic_name.startswith('#'):
                    topic_name = topic_name[1:]  # Remove # if present
                
                if topic_name:
                    topic, created = Topic.objects.get_or_create(
                        slug=topic_name.replace(' ', '-'),
                        defaults={'name': topic_name}
                    )
                    post.topics.add(topic)
                    topic.post_count = F('post_count') + 1
                    topic.save(update_fields=['post_count'])
            
            # Handle images
            for i, image in enumerate(images):
                PostImage.objects.create(
                    post=post,
                    image=image,
                    order=i
                )
            
            # Handle mentions
            self._process_mentions(post, mentioned_users)
            
            # Handle poll if poll post type
            if post.post_type == 'poll' and poll_options:
                self._create_poll(post, poll_options)
            
            return post
    
    def _process_mentions(self, post, mentioned_usernames):
        """Process @mentions in post content"""
        # Extract mentions from content
        content_mentions = re.findall(r'@(\w+)', post.content)
        all_mentions = set(mentioned_usernames + content_mentions)
        
        for username in all_mentions:
            try:
                user = User.objects.get(username=username)
                Mention.objects.create(
                    post=post,
                    mentioned_user=user,
                    mentioned_by=post.author
                )
            except User.DoesNotExist:
                pass
    
    def _create_poll(self, post, options):
        """Create poll options for the post"""
        # Create the poll
        poll = Poll.objects.create(
            post=post,
            multiple_choice=False,  # Default to single choice
            max_selections=1,
            anonymous_voting=False,
            show_results_before_vote=False,
            allow_result_view_without_vote=True
        )
        
        # Create poll options
        for i, option_text in enumerate(options):
            PollOption.objects.create(
                poll=poll,
                text=option_text.strip(),
                order=i
            )

class CommentCreateSerializer(serializers.ModelSerializer):
    """Enhanced serializer for creating comments"""
    mentioned_users = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Comment
        fields = ['parent', 'content', 'is_anonymous', 'mentioned_users']
    
    def validate_content(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Comment must be at least 2 characters long.")
        if len(value) > 2000:
            raise serializers.ValidationError("Comment must be less than 2000 characters.")
        return value
    
    def validate_parent(self, value):
        if value and value.parent:
            # Prevent deep nesting (only allow 2 levels)
            raise serializers.ValidationError("Cannot reply to a reply. Reply to the main comment instead.")
        return value
    
    def save(self, **kwargs):
        # This method is called by the view with post=post, author=request.user
        # We need to explicitly merge these with validated_data
        if hasattr(self, 'validated_data'):
            # Merge kwargs into validated_data
            self.validated_data.update(kwargs)
        return super().save()
    
    def create(self, validated_data):
        mentioned_users = validated_data.pop('mentioned_users', [])
        
        # Create comment with validated data
        
        with transaction.atomic():
            comment = Comment.objects.create(**validated_data)
            
            # Update counts
            comment.post.comment_count = F('comment_count') + 1
            comment.post.save()
            
            if comment.parent:
                comment.parent.reply_count = F('reply_count') + 1
                comment.parent.save()
            
            # Handle mentions
            self._process_mentions(comment, mentioned_users)
            
            return comment
    
    def _process_mentions(self, comment, mentioned_usernames):
        """Process @mentions in comment"""
        content_mentions = re.findall(r'@(\w+)', comment.content)
        all_mentions = set(mentioned_usernames + content_mentions)
        
        for username in all_mentions:
            try:
                user = User.objects.get(username=username)
                Mention.objects.create(
                    comment=comment,
                    mentioned_user=user,
                    mentioned_by=comment.author
                )
            except User.DoesNotExist:
                pass

class CommentSerializer(serializers.ModelSerializer):
    """Serializer for reading comments"""
    author = AuthorSerializer(read_only=True)
    time_since = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'content', 'is_anonymous', 'created_at', 
            'like_count', 'reply_count', 'time_since', 'is_liked',
            'can_edit', 'can_delete', 'replies'
        ]
    
    def get_time_since(self, obj):
        return timesince(obj.created_at)
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reactions.filter(user=request.user).exists()
        return False
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_edit(request.user)
        return False
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_delete(request.user)
        return False
    
    def get_replies(self, obj):
        # Get first few replies - avoid circular reference by limiting depth
        replies = obj.replies.order_by('created_at')[:3]
        # Use a simplified serializer for replies to avoid recursion
        reply_data = []
        for reply in replies:
            reply_data.append({
                'id': reply.id,
                'author': {
                    'id': reply.author.id,
                    'username': reply.author.username,
                    'display_name': reply.author.get_full_name() or reply.author.username,
                },
                'content': reply.content,
                'time_since': timesince(reply.created_at),
                'like_count': reply.like_count,
            })
        return reply_data

class PostBookmarkSerializer(serializers.ModelSerializer):
    post = PostListSerializer(read_only=True)
    
    class Meta:
        model = PostBookmark
        fields = ['id', 'post', 'created_at', 'notes']
        read_only_fields = ['created_at']

class PostReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostReport
        fields = ['id', 'post', 'reason', 'description', 'created_at']
        read_only_fields = ['created_at']
    
    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Please provide more details (at least 10 characters).")
        return value

class PostShareSerializer(serializers.Serializer):
    """Serializer for sharing posts"""
    platform = serializers.ChoiceField(choices=[p[0] for p in PostShare.PLATFORMS])
    message = serializers.CharField(required=False, allow_blank=True)

class TrendingPostSerializer(PostListSerializer):
    """Serializer for trending posts with additional metrics"""
    trending_score = serializers.FloatField(read_only=True)
    trending_position = serializers.IntegerField(read_only=True)
    
    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ['trending_score', 'trending_position']

class PostSearchSerializer(PostListSerializer):
    """Serializer for search results with highlights"""
    search_highlight = serializers.SerializerMethodField()
    
    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ['search_highlight']
    
    def get_search_highlight(self, obj):
        # Get search query from context
        request = self.context.get('request')
        if request:
            query = request.query_params.get('search', '')
            if query:
                # Find and highlight matching text
                import re
                pattern = re.compile(re.escape(query), re.IGNORECASE)
                
                # Check title
                if obj.title and pattern.search(obj.title):
                    return {
                        'field': 'title',
                        'text': obj.title,
                        'match': query
                    }
                
                # Check content
                if pattern.search(obj.content):
                    # Find the sentence containing the match
                    sentences = obj.content.split('.')
                    for sentence in sentences:
                        if pattern.search(sentence):
                            return {
                                'field': 'content',
                                'text': sentence.strip() + '.',
                                'match': query
                            }
        
        return None