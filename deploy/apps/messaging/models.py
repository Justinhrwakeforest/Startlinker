# startup_hub/apps/messaging/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from django.core.validators import FileExtensionValidator

User = get_user_model()

class Conversation(models.Model):
    """Conversation between users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name='conversations')
    is_group = models.BooleanField(default=False)
    group_name = models.CharField(max_length=100, blank=True)
    group_description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Job application context
    related_job_application = models.ForeignKey(
        'jobs.JobApplication', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='conversations'
    )
    conversation_type = models.CharField(
        max_length=20,
        choices=[
            ('general', 'General'),
            ('job_application', 'Job Application'),
            ('investor', 'Investor Interest'),
            ('mentorship', 'Mentorship'),
        ],
        default='general'
    )
    
    # Settings
    is_archived = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
        ]
    
    def __str__(self):
        if self.is_group:
            return self.group_name or f"Group ({self.participants.count()} members)"
        participants = list(self.participants.all()[:2])
        if len(participants) == 2:
            return f"{participants[0].username} & {participants[1].username}"
        return f"Conversation {self.id}"
    
    def get_other_participant(self, user):
        """Get the other participant in a 1-on-1 conversation"""
        if not self.is_group:
            return self.participants.exclude(id=user.id).first()
        return None

class Message(models.Model):
    """Individual messages in conversations"""
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('voice', 'Voice'),
        ('system', 'System'),
        ('call', 'Call'),
    ]
    
    # Call-related fields
    related_call = models.ForeignKey(
        'VideoCall', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='messages'
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(blank=True)
    
    # Message types
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    is_system_message = models.BooleanField(default=False)
    
    # Voice message fields
    voice_file = models.FileField(
        upload_to='voice_messages/%Y/%m/%d/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['webm', 'opus', 'ogg', 'mp3', 'wav'])]
    )
    voice_duration = models.FloatField(null=True, blank=True)  # Duration in seconds
    
    # Timestamps
    sent_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Moderation
    is_pinned = models.BooleanField(default=False)
    pinned_at = models.DateTimeField(null=True, blank=True)
    pinned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pinned_messages')
    is_announcement = models.BooleanField(default=False)
    
    # Reply to another message
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['sent_at']
        indexes = [
            models.Index(fields=['conversation', 'sent_at']),
            models.Index(fields=['sender', '-sent_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.sent_at}"

class MessageAttachment(models.Model):
    """File attachments for messages"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(
        upload_to='message_attachments/%Y/%m/%d/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'zip'])]
    )
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['uploaded_at']

class MessageReaction(models.Model):
    """Track emoji reactions to messages"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)  # Unicode emoji
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user', 'emoji']
        indexes = [
            models.Index(fields=['message', 'emoji']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to message {self.message.id}"

class MessageRead(models.Model):
    """Track read receipts"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
        indexes = [
            models.Index(fields=['user', '-read_at']),
        ]

class ConversationParticipant(models.Model):
    """Track participant-specific conversation settings"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participant_settings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Notifications
    is_muted = models.BooleanField(default=False)
    muted_until = models.DateTimeField(null=True, blank=True)
    
    # Last read
    last_read_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)
    
    # Labels/tags (using JSONField for SQLite compatibility)
    labels = models.JSONField(default=list, blank=True)  # ['Investor Interest', 'Hiring', etc.]
    
    class Meta:
        unique_together = ['conversation', 'user']
        indexes = [
            models.Index(fields=['user', '-joined_at']),
        ]

class ChatRequest(models.Model):
    """Request to start a conversation (for investor protection)"""
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_chat_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_chat_requests')
    message = models.TextField(help_text="Introduction message")
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    sent_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    
    # Created conversation (if accepted)
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['to_user', 'status', '-sent_at']),
            models.Index(fields=['from_user', '-sent_at']),
        ]
    
    def __str__(self):
        return f"Chat request from {self.from_user.username} to {self.to_user.username}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at

class UserConnection(models.Model):
    """Track connections between users"""
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_from')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_to')
    connected_at = models.DateTimeField(auto_now_add=True)
    
    # Connection context
    connection_type = models.CharField(max_length=50, blank=True)  # 'investor', 'founder', 'mentor', etc.
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['from_user', 'to_user']
        indexes = [
            models.Index(fields=['from_user', '-connected_at']),
            models.Index(fields=['to_user', '-connected_at']),
        ]
    
    @classmethod
    def are_connected(cls, user1, user2):
        return cls.objects.filter(
            models.Q(from_user=user1, to_user=user2) | 
            models.Q(from_user=user2, to_user=user1)
        ).exists()

class BlockedUser(models.Model):
    """Track blocked users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_users')
    blocked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    blocked_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['user', 'blocked_user']
        indexes = [
            models.Index(fields=['user', 'blocked_user']),
        ]

class BusinessCard(models.Model):
    """Business card information for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_card')
    
    # Professional Information
    full_name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    
    # Contact Information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    
    # Bio/Summary
    bio = models.TextField(max_length=500, blank=True)
    
    # Skills/Expertise
    skills = models.JSONField(default=list, blank=True)  # List of skills
    
    # Preferences
    is_public = models.BooleanField(default=True)  # Can be shared with anyone
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.title or 'Business Card'}"

class SharedBusinessCard(models.Model):
    """Track when business cards are shared in conversations"""
    card = models.ForeignKey(BusinessCard, on_delete=models.CASCADE, related_name='shares')
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_cards')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_cards')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='shared_cards')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='shared_cards')
    
    shared_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['card', 'shared_with', 'conversation']
        indexes = [
            models.Index(fields=['shared_with', '-shared_at']),
            models.Index(fields=['shared_by', '-shared_at']),
        ]

class VideoCall(models.Model):
    """Video call sessions in conversations"""
    CALL_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('answered', 'Answered'),
        ('ended', 'Ended'),
        ('missed', 'Missed'),
        ('declined', 'Declined'),
        ('failed', 'Failed'),
    ]
    
    CALL_TYPE_CHOICES = [
        ('video', 'Video Call'),
        ('audio', 'Audio Call'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='video_calls')
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_calls')
    participants = models.ManyToManyField(User, through='CallParticipant', related_name='video_calls')
    
    # Call metadata
    call_type = models.CharField(max_length=10, choices=CALL_TYPE_CHOICES, default='video')
    status = models.CharField(max_length=20, choices=CALL_STATUS_CHOICES, default='initiated')
    
    # WebRTC signaling data
    room_id = models.CharField(max_length=100, unique=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Call quality metrics
    quality_rating = models.PositiveSmallIntegerField(null=True, blank=True, 
        help_text="1-5 rating for call quality")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['conversation', '-created_at']),
            models.Index(fields=['caller', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_call_type_display()} call in {self.conversation} - {self.status}"
    
    @property
    def duration(self):
        """Get call duration in seconds"""
        if self.started_at and self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return 0
    
    def get_other_participants(self, user):
        """Get other participants excluding the given user"""
        return self.participants.exclude(id=user.id)

class CallParticipant(models.Model):
    """Track individual participant status in video calls"""
    PARTICIPANT_STATUS_CHOICES = [
        ('invited', 'Invited'),
        ('joined', 'Joined'),
        ('left', 'Left'),
        ('declined', 'Declined'),
        ('disconnected', 'Disconnected'),
    ]
    
    call = models.ForeignKey(VideoCall, on_delete=models.CASCADE, related_name='call_participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=PARTICIPANT_STATUS_CHOICES, default='invited')
    
    # WebRTC connection info
    peer_id = models.CharField(max_length=100, blank=True)
    is_video_enabled = models.BooleanField(default=True)
    is_audio_enabled = models.BooleanField(default=True)
    
    # Timestamps
    invited_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['call', 'user']
        indexes = [
            models.Index(fields=['call', 'status']),
            models.Index(fields=['user', '-invited_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} in call {self.call.id} - {self.status}"

class CallSignal(models.Model):
    """Store WebRTC signaling messages for call setup"""
    SIGNAL_TYPE_CHOICES = [
        ('offer', 'Offer'),
        ('answer', 'Answer'),
        ('ice-candidate', 'ICE Candidate'),
        ('call-end', 'Call End'),
    ]
    
    call = models.ForeignKey(VideoCall, on_delete=models.CASCADE, related_name='signals')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_signals')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_signals', null=True, blank=True)
    
    signal_type = models.CharField(max_length=20, choices=SIGNAL_TYPE_CHOICES)
    signal_data = models.JSONField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['call', 'signal_type', '-created_at']),
            models.Index(fields=['to_user', 'processed', '-created_at']),
        ]

class Poll(models.Model):
    """Poll created in a conversation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='polls')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_polls')
    
    # Poll details
    question = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    
    # Poll settings
    multiple_choice = models.BooleanField(default=False)  # Allow multiple selections
    anonymous = models.BooleanField(default=False)  # Hide voter identities
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    closes_at = models.DateTimeField(null=True, blank=True)  # Null means no expiry
    closed_at = models.DateTimeField(null=True, blank=True)  # Manual close
    is_closed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['conversation', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
        ]
    
    def __str__(self):
        return f"Poll: {self.question[:50]}..."
    
    @property
    def is_expired(self):
        return self.closes_at and timezone.now() > self.closes_at
    
    @property
    def total_votes(self):
        return sum(option.votes.count() for option in self.options.all())

class PollOption(models.Model):
    """Option in a poll"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['poll', 'order']),
        ]
    
    def __str__(self):
        return self.text
    
    @property
    def vote_count(self):
        return self.votes.count()
    
    @property
    def vote_percentage(self):
        total = self.poll.total_votes
        if total == 0:
            return 0
        return (self.vote_count / total) * 100

class PollVote(models.Model):
    """User's vote on a poll option"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messaging_poll_votes')
    voted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['option', 'user']  # One vote per user per option
        indexes = [
            models.Index(fields=['option', 'user']),
            models.Index(fields=['user', '-voted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} voted for {self.option.text}"

class Event(models.Model):
    """Event created in a conversation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='events')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    
    # Event details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=300, blank=True)
    
    # Timing
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    
    # Settings
    max_attendees = models.PositiveIntegerField(null=True, blank=True)  # Null means unlimited
    require_approval = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['starts_at']
        indexes = [
            models.Index(fields=['conversation', 'starts_at']),
            models.Index(fields=['created_by', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def attendee_count(self):
        return self.attendees.filter(status='going').count()
    
    @property
    def is_full(self):
        return self.max_attendees and self.attendee_count >= self.max_attendees

class EventAttendee(models.Model):
    """User's attendance status for an event"""
    STATUS_CHOICES = [
        ('going', 'Going'),
        ('maybe', 'Maybe'),
        ('not_going', 'Not Going'),
        ('pending', 'Pending Approval'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_attendances')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    responded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['event', 'user']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['user', '-responded_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.status})"