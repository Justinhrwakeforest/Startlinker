# startup_hub/apps/messaging/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from .models import (
    Conversation, Message, MessageAttachment, MessageRead, MessageReaction,
    ConversationParticipant, ChatRequest, UserConnection, BusinessCard, SharedBusinessCard,
    VideoCall, CallParticipant, CallSignal, Poll, PollOption, PollVote, Event, EventAttendee
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for messaging"""
    full_name = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'is_online']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
    
    def get_is_online(self, obj):
        # Check if user has been active in last 5 minutes
        if hasattr(obj, 'connect_profile') and obj.connect_profile.last_seen:
            return (timezone.now() - obj.connect_profile.last_seen).seconds < 300
        return False

class MessageAttachmentSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageAttachment
        fields = ['id', 'file', 'file_name', 'file_size', 'uploaded_at']
        read_only_fields = ['file_name', 'file_size', 'uploaded_at']
    
    def get_file(self, obj):
        """Get file URL, handling cases where request is not available"""
        request = self.context.get('request')
        if request and hasattr(request, 'build_absolute_uri'):
            return request.build_absolute_uri(obj.file.url) if obj.file else None
        else:
            # Fallback for when request is not available
            return obj.file.url if obj.file else None

class MessageReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ['id', 'user', 'emoji', 'created_at']
        read_only_fields = ['created_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    reaction_counts = serializers.SerializerMethodField()
    user_reactions = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    read_receipts = serializers.SerializerMethodField()
    voice_duration = serializers.SerializerMethodField()
    voice_file = serializers.SerializerMethodField()
    pinned_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'content', 'sent_at',
            'edited_at', 'is_deleted', 'is_system_message',
            'reply_to', 'attachments', 'reactions', 'reaction_counts', 
            'user_reactions', 'is_read', 'read_receipts', 'message_type', 'voice_file', 'voice_duration',
            'is_pinned', 'pinned_at', 'pinned_by', 'is_announcement'
        ]
        read_only_fields = ['sent_at', 'edited_at']
    
    def get_reaction_counts(self, obj):
        """Get count of each emoji reaction"""
        from django.db.models import Count
        counts = {}
        reaction_counts = obj.reactions.values('emoji').annotate(count=Count('emoji'))
        for item in reaction_counts:
            counts[item['emoji']] = item['count']
        return counts
    
    def get_user_reactions(self, obj):
        """Get current user's reactions to this message"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return list(obj.reactions.filter(user=request.user).values_list('emoji', flat=True))
        return []
    
    def get_is_read(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.read_receipts.filter(user=request.user).exists()
        return False
    
    def get_read_receipts(self, obj):
        """Get read receipts for this message"""
        from .models import MessageRead
        read_receipts = MessageRead.objects.filter(message=obj).select_related('user')
        return [
            {
                'user_id': receipt.user.id,
                'user': {
                    'id': receipt.user.id,
                    'username': receipt.user.username,
                    'full_name': receipt.user.get_full_name() or receipt.user.username
                },
                'read_at': receipt.read_at.isoformat()
            } for receipt in read_receipts
        ]
    
    def get_voice_duration(self, obj):
        """Get voice duration, ensuring it's JSON-serializable"""
        import math
        if obj.voice_duration is None:
            return None
        
        # Check for invalid float values
        if math.isinf(obj.voice_duration) or math.isnan(obj.voice_duration):
            return None
            
        return obj.voice_duration
    
    def get_voice_file(self, obj):
        """Get voice file URL, handling cases where request is not available"""
        if not obj.voice_file:
            return None
            
        request = self.context.get('request')
        if request and hasattr(request, 'build_absolute_uri'):
            return request.build_absolute_uri(obj.voice_file.url)
        else:
            # Fallback for when request is not available
            return obj.voice_file.url

class ConversationParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ConversationParticipant
        fields = [
            'user', 'is_muted', 'muted_until', 'joined_at',
            'left_at', 'is_admin', 'labels'
        ]

class ConversationListSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'is_group', 'group_name', 'created_at', 'updated_at',
            'other_participant', 'last_message', 'unread_count', 'display_name'
        ]
    
    def get_other_participant(self, obj):
        if not obj.is_group:
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                other = obj.get_other_participant(request.user)
                if other:
                    return UserSerializer(other).data
        return None
    
    def get_last_message(self, obj):
        last_message = obj.messages.filter(is_deleted=False).last()
        if last_message:
            return MessageSerializer(last_message, context=self.context).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                participant = obj.participant_settings.get(user=request.user)
                if participant.last_read_message:
                    return obj.messages.filter(
                        sent_at__gt=participant.last_read_message.sent_at,
                        is_deleted=False
                    ).exclude(sender=request.user).count()
                else:
                    return obj.messages.filter(is_deleted=False).exclude(sender=request.user).count()
            except ConversationParticipant.DoesNotExist:
                return 0
        return 0
    
    def get_display_name(self, obj):
        if obj.is_group:
            return obj.group_name or f"Group Chat ({obj.participants.count()} members)"
        else:
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                other = obj.get_other_participant(request.user)
                if other:
                    return other.get_full_name() or other.username
                else:
                    # Handle edge case where conversation has only current user
                    # or no other participant found
                    participants = obj.participants.exclude(id=request.user.id)
                    if participants.exists():
                        other_user = participants.first()
                        return other_user.get_full_name() or other_user.username
                    else:
                        # Single participant conversation - shouldn't happen but handle gracefully
                        return f"Chat with {request.user.get_full_name() or request.user.username}"
        return "Unknown Conversation"

class ConversationDetailSerializer(ConversationListSerializer):
    participants = UserSerializer(many=True, read_only=True)
    participant_settings = ConversationParticipantSerializer(many=True, read_only=True)
    messages = serializers.SerializerMethodField()
    
    class Meta(ConversationListSerializer.Meta):
        fields = ConversationListSerializer.Meta.fields + [
            'participants', 'participant_settings', 'messages',
            'group_description', 'is_archived', 'is_muted'
        ]
    
    def get_messages(self, obj):
        # Get last 50 messages
        messages = obj.messages.filter(is_deleted=False).order_by('-sent_at')[:50]
        return MessageSerializer(
            reversed(messages), 
            many=True, 
            context=self.context
        ).data

class ConversationCreateSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )
    initial_message = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Conversation
        fields = ['participant_ids', 'initial_message', 'is_group', 'group_name']
    
    def validate_participant_ids(self, value):
        if len(value) < 1:
            raise serializers.ValidationError("At least one other participant is required")
        
        # Check if all users exist
        users = User.objects.filter(id__in=value)
        if users.count() != len(value):
            raise serializers.ValidationError("Some participant IDs are invalid")
        
        # Ensure the current user is not trying to add themselves
        request = self.context.get('request')
        if request and request.user.id in value:
            raise serializers.ValidationError("You cannot add yourself as a participant")
        
        return value
    
    def create(self, validated_data):
        try:
            participant_ids = validated_data.pop('participant_ids')
            initial_message = validated_data.pop('initial_message', None)
            request_user = self.context['request'].user
            
            # Add request user to participants
            all_participant_ids = set(participant_ids + [request_user.id])
            
            # Check if this is a group chat
            is_group = len(all_participant_ids) > 2 or validated_data.get('is_group', False)
            
            # For 1-on-1 chats, check if conversation already exists
            if not is_group and len(all_participant_ids) == 2:
                existing = Conversation.objects.filter(
                    is_group=False,
                    participants__in=all_participant_ids
                ).annotate(
                    participant_count=Count('participants')
                ).filter(participant_count=2)
                
                if existing.exists():
                    return existing.first()
            
            # Prepare conversation data
            conversation_data = {
                'is_group': is_group,
                'created_by': request_user,
            }
            
            # Only include group_name if it's a group chat
            if is_group and 'group_name' in validated_data:
                conversation_data['group_name'] = validated_data['group_name']
            
            # Create conversation
            conversation = Conversation.objects.create(**conversation_data)
            
            # Add participants
            participants = User.objects.filter(id__in=all_participant_ids)
            conversation.participants.set(participants)
            
            # Create participant settings
            for participant in participants:
                ConversationParticipant.objects.create(
                    conversation=conversation,
                    user=participant,
                    is_admin=(participant == request_user)
                )
            
            # Send initial message if provided
            if initial_message:
                Message.objects.create(
                    conversation=conversation,
                    sender=request_user,
                    content=initial_message
                )
            
            return conversation
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating conversation: {e}")
            logger.error(f"Validated data: {validated_data}")
            logger.error(f"Request user: {request_user}")
            raise serializers.ValidationError(f"Failed to create conversation: {str(e)}")

class MessageCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )
    content = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Message
        fields = ['conversation', 'content', 'reply_to', 'attachments', 'message_type']
    
    def validate(self, data):
        """Ensure either content or attachments are provided"""
        content = data.get('content', '').strip()
        attachments = data.get('attachments', [])
        message_type = data.get('message_type', 'text')
        
        # Also check request.FILES for attachments when sent via FormData
        request = self.context.get('request')
        if request and hasattr(request, 'FILES'):
            attachments = attachments or request.FILES.getlist('attachments')
        
        # For voice messages, we'll handle the audio file separately
        if message_type == 'voice':
            return data
            
        if not content and not attachments:
            raise serializers.ValidationError("Either content or attachments must be provided")
        
        return data
    
    def create(self, validated_data):
        # Handle attachments from request.FILES
        request = self.context.get('request')
        attachments = []
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"MessageCreateSerializer.create called")
        logger.error(f"Request user: {request.user if request else 'No request'}")
        logger.error(f"Validated data: {validated_data}")
        logger.error(f"Request FILES: {request.FILES if request and hasattr(request, 'FILES') else 'No FILES'}")
        
        if request and hasattr(request, 'FILES'):
            # Get files from request.FILES (when sent via FormData)
            attachments = request.FILES.getlist('attachments')
            logger.error(f"Found {len(attachments)} attachments in FILES")
        else:
            # Get from validated_data (when sent as JSON)
            attachments = validated_data.pop('attachments', [])
            logger.error(f"Found {len(attachments)} attachments in validated_data")
        
        # Remove attachments from validated_data if present (to avoid conflict)
        validated_data.pop('attachments', None)
        
        message = Message.objects.create(**validated_data)
        logger.error(f"Created message: {message.id}")
        
        # Create attachments
        for file in attachments:
            attachment = MessageAttachment.objects.create(
                message=message,
                file=file,
                file_name=file.name,
                file_size=file.size
            )
            logger.error(f"Created attachment: {attachment.id}")
        
        # Update conversation's updated_at
        message.conversation.save()
        
        return message

class VoiceMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer specifically for creating voice messages"""
    audio = serializers.FileField(write_only=True, required=True)
    duration = serializers.FloatField(write_only=True, required=False)
    
    class Meta:
        model = Message
        fields = ['conversation', 'audio', 'duration', 'message_type']
    
    def validate_audio(self, value):
        """Validate audio file"""
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Audio file too large. Max size is 10MB")
        
        # Validate file extension
        allowed_extensions = ['webm', 'opus', 'ogg', 'mp3', 'wav']
        ext = value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
        
        return value
    
    def create(self, validated_data):
        """Create voice message"""
        import math
        audio_file = validated_data.pop('audio')
        duration = validated_data.pop('duration', None)
        
        # Validate duration
        if duration is not None and (math.isinf(duration) or math.isnan(duration) or duration < 0):
            duration = None
        
        # Create the message
        message = Message.objects.create(
            conversation=validated_data['conversation'],
            sender=self.context['request'].user,
            message_type='voice',
            voice_file=audio_file,
            voice_duration=duration,
            content=f"🎤 Voice message ({duration:.1f}s)" if duration else "🎤 Voice message"
        )
        
        # Update conversation's updated_at
        message.conversation.save()
        
        return message

class ChatRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    to_user_id = serializers.IntegerField(write_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRequest
        fields = [
            'id', 'from_user', 'to_user', 'to_user_id', 'message',
            'status', 'sent_at', 'responded_at', 'expires_at', 'is_expired'
        ]
        read_only_fields = ['status', 'sent_at', 'responded_at', 'expires_at']
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def validate_to_user_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value
    
    def validate_message(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters")
        if len(value) > 500:
            raise serializers.ValidationError("Message must be less than 500 characters")
        return value
    
    def create(self, validated_data):
        to_user_id = validated_data.pop('to_user_id')
        to_user = User.objects.get(id=to_user_id)
        
        # Set expiration (7 days)
        expires_at = timezone.now() + timedelta(days=7)
        
        return ChatRequest.objects.create(
            to_user=to_user,
            expires_at=expires_at,
            **validated_data
        )

class UserConnectionSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    is_mutual = serializers.SerializerMethodField()
    
    class Meta:
        model = UserConnection
        fields = [
            'id', 'from_user', 'to_user', 'connected_at',
            'connection_type', 'notes', 'is_mutual'
        ]
    
    def get_is_mutual(self, obj):
        return UserConnection.objects.filter(
            from_user=obj.to_user,
            to_user=obj.from_user
        ).exists()

class BusinessCardSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BusinessCard
        fields = [
            'id', 'user', 'full_name', 'title', 'company', 'industry',
            'email', 'phone', 'website', 'linkedin', 'bio', 'skills',
            'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class SharedBusinessCardSerializer(serializers.ModelSerializer):
    card = BusinessCardSerializer(read_only=True)
    shared_by = UserSerializer(read_only=True)
    shared_with = UserSerializer(read_only=True)
    
    class Meta:
        model = SharedBusinessCard
        fields = ['id', 'card', 'shared_by', 'shared_with', 'conversation', 'message', 'shared_at']
        read_only_fields = ['shared_at']

class CallParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CallParticipant
        fields = [
            'id', 'user', 'status', 'peer_id', 'is_video_enabled', 'is_audio_enabled',
            'invited_at', 'joined_at', 'left_at'
        ]
        read_only_fields = ['invited_at', 'joined_at', 'left_at']

class VideoCallSerializer(serializers.ModelSerializer):
    caller = UserSerializer(read_only=True)
    participants = UserSerializer(many=True, read_only=True)
    call_participants = CallParticipantSerializer(many=True, read_only=True)
    conversation = serializers.StringRelatedField(read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = VideoCall
        fields = [
            'id', 'conversation', 'caller', 'participants', 'call_participants',
            'call_type', 'status', 'room_id', 'created_at', 'started_at', 'ended_at',
            'quality_rating', 'duration_seconds'
        ]
        read_only_fields = ['created_at', 'started_at', 'ended_at', 'room_id']
    
    def get_duration_seconds(self, obj):
        """Get call duration in seconds"""
        return obj.duration

class CallSignalSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    call = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = CallSignal
        fields = [
            'id', 'call', 'from_user', 'to_user', 'signal_type', 'signal_data',
            'created_at', 'processed'
        ]
        read_only_fields = ['created_at', 'processed']
    
    def validate_signal_data(self, value):
        """Validate signal data based on signal type"""
        signal_type = self.initial_data.get('signal_type')
        
        if signal_type in ['offer', 'answer']:
            required_fields = ['sdp', 'type']
            if not all(field in value for field in required_fields):
                raise serializers.ValidationError(f"Signal type '{signal_type}' requires: {required_fields}")
        
        elif signal_type == 'ice-candidate':
            required_fields = ['candidate', 'sdpMLineIndex', 'sdpMid']
            if not all(field in value for field in required_fields):
                raise serializers.ValidationError(f"ICE candidate requires: {required_fields}")
        
        return value

# Poll serializers
class PollVoteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PollVote
        fields = ['id', 'user', 'voted_at']
        read_only_fields = ['voted_at']

class PollOptionSerializer(serializers.ModelSerializer):
    vote_count = serializers.ReadOnlyField()
    vote_percentage = serializers.ReadOnlyField()
    votes = PollVoteSerializer(many=True, read_only=True)
    user_voted = serializers.SerializerMethodField()
    
    class Meta:
        model = PollOption
        fields = ['id', 'text', 'order', 'vote_count', 'vote_percentage', 'votes', 'user_voted']
        read_only_fields = ['vote_count', 'vote_percentage']
    
    def get_user_voted(self, obj):
        """Check if current user has voted for this option"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.votes.filter(user=request.user).exists()
        return False

class PollSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    options = PollOptionSerializer(many=True, read_only=True)
    total_votes = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    user_votes = serializers.SerializerMethodField()
    
    class Meta:
        model = Poll
        fields = [
            'id', 'question', 'description', 'multiple_choice', 'anonymous',
            'created_by', 'created_at', 'closes_at', 'closed_at', 'is_closed',
            'options', 'total_votes', 'is_expired', 'user_votes'
        ]
        read_only_fields = ['created_by', 'created_at', 'closed_at', 'total_votes', 'is_expired']
    
    def get_user_votes(self, obj):
        """Get current user's votes for this poll"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user_votes = PollVote.objects.filter(
                option__poll=obj,
                user=request.user
            ).values_list('option_id', flat=True)
            return list(user_votes)
        return []

# Event serializers
class EventAttendeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = EventAttendee
        fields = ['id', 'user', 'status', 'responded_at', 'updated_at']
        read_only_fields = ['responded_at', 'updated_at']

class EventSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    attendees = EventAttendeeSerializer(many=True, read_only=True)
    attendee_count = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    user_attendance = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'location', 'starts_at', 'ends_at',
            'all_day', 'max_attendees', 'require_approval', 'is_cancelled',
            'created_by', 'created_at', 'updated_at', 'attendees',
            'attendee_count', 'is_full', 'user_attendance'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'attendee_count', 'is_full']
    
    def get_user_attendance(self, obj):
        """Get current user's attendance status"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                attendee = obj.attendees.get(user=request.user)
                return attendee.status
            except EventAttendee.DoesNotExist:
                return None
        return None