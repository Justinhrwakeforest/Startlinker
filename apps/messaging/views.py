# startup_hub/apps/messaging/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count, Max, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

from .models import (
    Conversation, Message, MessageAttachment, MessageRead, MessageReaction,
    ConversationParticipant, ChatRequest, UserConnection, BlockedUser, BusinessCard, SharedBusinessCard,
    VideoCall, CallParticipant, CallSignal
)
from .serializers import (
    ConversationListSerializer, ConversationDetailSerializer,
    ConversationCreateSerializer, MessageSerializer, MessageCreateSerializer,
    ChatRequestSerializer, UserConnectionSerializer, MessageReactionSerializer,
    BusinessCardSerializer, SharedBusinessCardSerializer, VoiceMessageCreateSerializer,
    VideoCallSerializer, CallParticipantSerializer, CallSignalSerializer
)

class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for conversations"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Get conversations where user is a participant
        queryset = Conversation.objects.filter(
            participants=user
        ).annotate(
            last_message_time=Max('messages__sent_at')
        ).order_by('-last_message_time')
        
        # Filter by conversation type
        conv_type = self.request.query_params.get('type')
        if conv_type == 'group':
            queryset = queryset.filter(is_group=True)
        elif conv_type == 'direct':
            queryset = queryset.filter(is_group=False)
        
        # Filter archived
        show_archived = self.request.query_params.get('archived', 'false').lower() == 'true'
        if not show_archived:
            queryset = queryset.filter(is_archived=False)
        
        return queryset.prefetch_related('participants', 'messages')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        elif self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationListSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        
        # Return detailed serializer
        detail_serializer = ConversationDetailSerializer(
            conversation,
            context={'request': request}
        )
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive/unarchive conversation"""
        conversation = self.get_object()
        conversation.is_archived = not conversation.is_archived
        conversation.save()
        
        return Response({
            'archived': conversation.is_archived,
            'message': 'Conversation archived' if conversation.is_archived else 'Conversation unarchived'
        })
    
    @action(detail=True, methods=['post'])
    def mute(self, request, pk=None):
        """Mute/unmute conversation"""
        conversation = self.get_object()
        participant, created = ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=request.user
        )
        
        participant.is_muted = not participant.is_muted
        if participant.is_muted:
            # Set mute duration (e.g., 8 hours)
            duration = request.data.get('duration', 8)
            participant.muted_until = timezone.now() + timedelta(hours=duration)
        else:
            participant.muted_until = None
        
        participant.save()
        
        return Response({
            'muted': participant.is_muted,
            'muted_until': participant.muted_until
        })
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a group conversation"""
        conversation = self.get_object()
        
        if not conversation.is_group:
            return Response(
                {'error': 'Cannot leave direct conversations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conversation.participants.remove(request.user)
        
        # Add system message
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=f"{request.user.get_full_name() or request.user.username} left the group",
            is_system_message=True
        )
        
        return Response({'message': 'Left conversation successfully'})
    
    @action(detail=True, methods=['post'])
    def clear_messages(self, request, pk=None):
        """Clear all messages in a conversation"""
        conversation = self.get_object()
        
        # Check if user is a participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete all messages (soft delete)
        deleted_count = conversation.messages.update(
            is_deleted=True,
            deleted_at=timezone.now()
        )
        
        # Add system message about clearing chat
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=f"{request.user.get_full_name() or request.user.username} cleared the chat",
            is_system_message=True
        )
        
        return Response({
            'message': f'Successfully cleared {deleted_count} messages',
            'deleted_count': deleted_count
        })
    
    @action(detail=True, methods=['post'])
    def add_participants(self, request, pk=None):
        """Add participants to a group conversation"""
        conversation = self.get_object()
        
        # Only group conversations can have participants added
        if not conversation.is_group:
            return Response(
                {'error': 'Cannot add participants to direct conversations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is an admin or moderator
        try:
            participant = ConversationParticipant.objects.get(
                conversation=conversation,
                user=request.user
            )
            if not (participant.is_admin or participant.is_moderator):
                return Response(
                    {'error': 'Only admins and moderators can add participants'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except ConversationParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get participant IDs from request
        participant_ids = request.data.get('participant_ids', [])
        if not participant_ids:
            return Response(
                {'error': 'No participant IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate that users exist
        users = User.objects.filter(id__in=participant_ids)
        if users.count() != len(participant_ids):
            return Response(
                {'error': 'Some user IDs are invalid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filter out users who are already participants
        existing_participant_ids = list(conversation.participants.values_list('id', flat=True))
        new_users = users.exclude(id__in=existing_participant_ids)
        
        if not new_users.exists():
            return Response(
                {'error': 'All specified users are already participants'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add new participants
        added_count = 0
        for user in new_users:
            conversation.participants.add(user)
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=user,
                is_admin=False,
                is_moderator=False
            )
            added_count += 1
        
        # Create system message
        user_names = [user.get_full_name() or user.username for user in new_users]
        if len(user_names) == 1:
            message_content = f"{request.user.get_full_name() or request.user.username} added {user_names[0]} to the group"
        else:
            message_content = f"{request.user.get_full_name() or request.user.username} added {', '.join(user_names)} to the group"
        
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content,
            is_system_message=True
        )
        
        return Response({
            'message': f'Successfully added {added_count} participant(s)',
            'added_count': added_count,
            'added_users': [{'id': user.id, 'username': user.username} for user in new_users]
        })
    
    @action(detail=True, methods=['delete'])
    def delete_conversation(self, request, pk=None):
        """Delete entire conversation (only for direct messages or if user is admin in group)"""
        conversation = self.get_object()
        
        # Check if user is a participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # For group conversations, only admins can delete
        if conversation.is_group:
            participant = ConversationParticipant.objects.filter(
                conversation=conversation,
                user=request.user
            ).first()
            
            if not participant or not participant.is_admin:
                return Response(
                    {'error': 'Only group admins can delete the conversation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Delete the conversation
        conversation.delete()
        
        return Response({'message': 'Conversation deleted successfully'})
    
    @action(detail=True, methods=['post'])
    def update_tags(self, request, pk=None):
        """Update conversation tags for the current user"""
        conversation = self.get_object()
        
        # Check if user is a participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        tags = request.data.get('tags', [])
        
        # Get or create participant settings
        participant, created = ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=request.user
        )
        
        # Update tags
        participant.labels = tags
        participant.save()
        
        return Response({
            'message': 'Tags updated successfully',
            'tags': tags
        })
    
    @action(detail=True, methods=['get'])
    def get_tags(self, request, pk=None):
        """Get conversation tags for the current user"""
        conversation = self.get_object()
        
        # Check if user is a participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            participant = ConversationParticipant.objects.get(
                conversation=conversation,
                user=request.user
            )
            tags = participant.labels or []
        except ConversationParticipant.DoesNotExist:
            tags = []
        
        return Response({'tags': tags})
    
    @action(detail=True, methods=['post'])
    def promote_moderator(self, request, pk=None):
        """Promote a user to moderator role"""
        conversation = self.get_object()
        
        # Check if user is admin
        participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user=request.user
        ).first()
        
        if not participant or not participant.is_admin:
            return Response(
                {'error': 'Only admins can promote users to moderator'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get target participant
        target_participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user_id=user_id
        ).first()
        
        if not target_participant:
            return Response(
                {'error': 'User is not a participant in this conversation'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Promote to moderator
        target_participant.is_moderator = True
        target_participant.save()
        
        # Create system message
        target_user = target_participant.user
        message_content = f"{request.user.get_full_name() or request.user.username} promoted {target_user.get_full_name() or target_user.username} to moderator"
        
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content,
            is_system_message=True
        )
        
        return Response({'message': 'User promoted to moderator successfully'})
    
    @action(detail=True, methods=['post'])
    def promote_admin(self, request, pk=None):
        """Promote a user to admin role"""
        conversation = self.get_object()
        
        # Check if user is admin
        participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user=request.user
        ).first()
        
        if not participant or not participant.is_admin:
            return Response(
                {'error': 'Only admins can promote users to admin'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get target participant
        target_participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user_id=user_id
        ).first()
        
        if not target_participant:
            return Response(
                {'error': 'User is not a participant in this conversation'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Promote to admin
        target_participant.is_admin = True
        target_participant.is_moderator = True  # Admins are also moderators
        target_participant.save()
        
        # Create system message
        target_user = target_participant.user
        message_content = f"{request.user.get_full_name() or request.user.username} promoted {target_user.get_full_name() or target_user.username} to admin"
        
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content,
            is_system_message=True
        )
        
        return Response({'message': 'User promoted to admin successfully'})
    
    @action(detail=True, methods=['post'])
    def demote(self, request, pk=None):
        """Demote a user to regular member"""
        conversation = self.get_object()
        
        # Check if user is admin
        participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user=request.user
        ).first()
        
        if not participant or not participant.is_admin:
            return Response(
                {'error': 'Only admins can demote users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get target participant
        target_participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user_id=user_id
        ).first()
        
        if not target_participant:
            return Response(
                {'error': 'User is not a participant in this conversation'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Can't demote yourself if you're the only admin
        if target_participant.user_id == request.user.id:
            admin_count = ConversationParticipant.objects.filter(
                conversation=conversation,
                is_admin=True
            ).count()
            
            if admin_count <= 1:
                return Response(
                    {'error': 'Cannot demote yourself as the only admin'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Demote to regular member
        old_role = 'admin' if target_participant.is_admin else 'moderator'
        target_participant.is_admin = False
        target_participant.is_moderator = False
        target_participant.save()
        
        # Create system message
        target_user = target_participant.user
        message_content = f"{request.user.get_full_name() or request.user.username} demoted {target_user.get_full_name() or target_user.username} from {old_role} to member"
        
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content,
            is_system_message=True
        )
        
        return Response({'message': 'User demoted successfully'})
    
    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """Remove a user from the group"""
        conversation = self.get_object()
        
        # Check if user is admin or moderator
        participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user=request.user
        ).first()
        
        if not participant or not (participant.is_admin or participant.is_moderator):
            return Response(
                {'error': 'Only admins and moderators can remove participants'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get target participant
        target_participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user_id=user_id
        ).first()
        
        if not target_participant:
            return Response(
                {'error': 'User is not a participant in this conversation'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Can't remove yourself
        if target_participant.user_id == request.user.id:
            return Response(
                {'error': 'Cannot remove yourself from the group'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only admins can remove other admins
        if target_participant.is_admin and not participant.is_admin:
            return Response(
                {'error': 'Only admins can remove other admins'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Moderators can't remove other moderators (unless they're admin)
        if target_participant.is_moderator and not participant.is_admin:
            return Response(
                {'error': 'Only admins can remove moderators'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Remove participant
        target_user = target_participant.user
        conversation.participants.remove(target_user)
        target_participant.delete()
        
        # Create system message
        message_content = f"{request.user.get_full_name() or request.user.username} removed {target_user.get_full_name() or target_user.username} from the group"
        
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content,
            is_system_message=True
        )
        
        return Response({'message': 'User removed from group successfully'})

class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for messages"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Message.objects.filter(
            conversation__participants=self.request.user,
            is_deleted=False
        )
        
        # Filter by conversation
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        
        return queryset.select_related('sender', 'reply_to').order_by('sent_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    def get_serializer_context(self):
        """Add request to serializer context"""
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
    def create(self, request, *args, **kwargs):
        """Create a new message and return full message data"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.error(f"MessageViewSet.create called by user: {request.user}")
        logger.error(f"Request data: {request.data}")
        logger.error(f"Request FILES: {request.FILES}")
        
        try:
            serializer = self.get_serializer(data=request.data)
            logger.error(f"Serializer created: {serializer}")
            
            if not serializer.is_valid():
                logger.error(f"Serializer validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            logger.error("Serializer validation passed, saving...")
            message = serializer.save(sender=request.user)
            
            # Update conversation's updated_at
            message.conversation.save()
            
            # Mark as read by sender
            MessageRead.objects.create(message=message, user=request.user)
            
            # Return full message data using MessageSerializer
            response_serializer = MessageSerializer(message, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Exception in MessageViewSet.create: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete message"""
        message = self.get_object()
        
        if message.sender != request.user:
            return Response(
                {'error': 'You can only delete your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.save()
        
        return Response({'message': 'Message deleted'})
    
    @action(detail=True, methods=['post'])
    def edit(self, request, pk=None):
        """Edit message"""
        message = self.get_object()
        
        if message.sender != request.user:
            return Response(
                {'error': 'You can only edit your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if message is too old to edit (e.g., 15 minutes)
        if timezone.now() - message.sent_at > timedelta(minutes=15):
            return Response(
                {'error': 'Message is too old to edit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.content = request.data.get('content', message.content)
        message.edited_at = timezone.now()
        message.save()
        
        serializer = self.get_serializer(message)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """Pin/unpin a message"""
        message = self.get_object()
        conversation = message.conversation
        
        # Check if user is admin or moderator
        try:
            participant = ConversationParticipant.objects.get(
                conversation=conversation,
                user=request.user
            )
            if not (participant.is_admin or participant.is_moderator):
                return Response(
                    {'error': 'Only admins and moderators can pin messages'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except ConversationParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Toggle pin status
        message.is_pinned = not message.is_pinned
        if message.is_pinned:
            message.pinned_at = timezone.now()
            message.pinned_by = request.user
        else:
            message.pinned_at = None
            message.pinned_by = None
        message.save()
        
        # Create system message
        system_msg = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=f"{request.user.username} {'pinned' if message.is_pinned else 'unpinned'} a message",
            is_system_message=True
        )
        
        return Response({
            'pinned': message.is_pinned,
            'message': MessageSerializer(message, context={'request': request}).data
        })
    
    @action(detail=True, methods=['post'])
    def announce(self, request, pk=None):
        """Mark message as announcement"""
        message = self.get_object()
        conversation = message.conversation
        
        # Check if user is admin
        try:
            participant = ConversationParticipant.objects.get(
                conversation=conversation,
                user=request.user
            )
            if not participant.is_admin:
                return Response(
                    {'error': 'Only admins can create announcements'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except ConversationParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Toggle announcement status
        message.is_announcement = not message.is_announcement
        message.save()
        
        return Response({
            'is_announcement': message.is_announcement,
            'message': MessageSerializer(message, context={'request': request}).data
        })
    
    @action(detail=False, methods=['get'])
    def pinned(self, request):
        """Get pinned messages in a conversation"""
        conversation_id = request.query_params.get('conversation')
        
        if not conversation_id:
            return Response(
                {'error': 'Conversation ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is participant
        if not Conversation.objects.filter(
            id=conversation_id,
            participants=request.user
        ).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        messages = Message.objects.filter(
            conversation_id=conversation_id,
            is_pinned=True,
            is_deleted=False
        ).order_by('-pinned_at')
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Add or remove reaction to message"""
        message = self.get_object()
        emoji = request.data.get('emoji')
        
        if not emoji:
            return Response(
                {'error': 'Emoji is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user can access this message
        if not message.conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'You cannot react to messages in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Toggle reaction
        reaction, created = MessageReaction.objects.get_or_create(
            message=message,
            user=request.user,
            emoji=emoji
        )
        
        if not created:
            # Remove existing reaction
            reaction.delete()
            return Response({'message': 'Reaction removed', 'added': False})
        
        return Response({
            'message': 'Reaction added',
            'added': True,
            'reaction': MessageReactionSerializer(reaction).data
        })
    
    @action(detail=True, methods=['get'])
    def reactions(self, request, pk=None):
        """Get all reactions for a message"""
        message = self.get_object()
        
        # Check if user can access this message
        if not message.conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'You cannot view reactions in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reactions = message.reactions.all().order_by('created_at')
        serializer = MessageReactionSerializer(reactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search messages"""
        query = request.query_params.get('q', '').strip()
        conversation_id = request.query_params.get('conversation')
        
        if not query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Base queryset - only messages in conversations user participates in
        queryset = Message.objects.filter(
            conversation__participants=request.user,
            is_deleted=False
        )
        
        # Filter by conversation if specified
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        
        # Search in message content
        queryset = queryset.filter(
            content__icontains=query
        ).select_related('sender', 'conversation').order_by('-sent_at')
        
        # Limit results
        queryset = queryset[:50]
        
        # Serialize results
        serializer = MessageSerializer(queryset, many=True, context={'request': request})
        return Response({
            'results': serializer.data,
            'count': len(serializer.data),
            'query': query
        })
    
    @action(detail=True, methods=['post'])
    def share_business_card(self, request, pk=None):
        """Share business card in a message"""
        message = self.get_object()
        
        # Check if user can access this message
        if not message.conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'You cannot share business cards in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get or create user's business card
        try:
            business_card = BusinessCard.objects.get(user=request.user)
        except BusinessCard.DoesNotExist:
            return Response(
                {'error': 'You need to create a business card first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get other participants
        other_participants = message.conversation.participants.exclude(id=request.user.id)
        
        shared_cards = []
        for participant in other_participants:
            shared_card, created = SharedBusinessCard.objects.get_or_create(
                card=business_card,
                shared_by=request.user,
                shared_with=participant,
                conversation=message.conversation,
                defaults={'message': message}
            )
            if created:
                shared_cards.append(shared_card)
        
        # Create a system message about the business card share
        system_message = Message.objects.create(
            conversation=message.conversation,
            sender=request.user,
            content=f"{request.user.get_full_name() or request.user.username} shared their business card",
            is_system_message=True
        )
        
        return Response({
            'message': 'Business card shared successfully',
            'shared_with': len(shared_cards),
            'system_message': MessageSerializer(system_message, context={'request': request}).data
        })

class ChatRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for chat requests"""
    serializer_class = ChatRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        request_type = self.request.query_params.get('type', 'received')
        
        if request_type == 'sent':
            queryset = ChatRequest.objects.filter(from_user=user)
        else:
            queryset = ChatRequest.objects.filter(to_user=user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Exclude expired
        queryset = queryset.exclude(
            status='pending',
            expires_at__lt=timezone.now()
        )
        
        return queryset.select_related('from_user', 'to_user').order_by('-sent_at')
    
    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept chat request"""
        chat_request = self.get_object()
        
        if chat_request.to_user != request.user:
            return Response(
                {'error': 'You can only accept requests sent to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if chat_request.status != 'pending':
            return Response(
                {'error': 'Request is no longer pending'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create conversation
        conversation = Conversation.objects.create(is_group=False)
        conversation.participants.add(chat_request.from_user, chat_request.to_user)
        
        # Create initial message
        Message.objects.create(
            conversation=conversation,
            sender=chat_request.from_user,
            content=chat_request.message
        )
        
        # Update request
        chat_request.status = 'accepted'
        chat_request.responded_at = timezone.now()
        chat_request.conversation = conversation
        chat_request.save()
        
        # Create connection
        UserConnection.objects.create(
            from_user=chat_request.from_user,
            to_user=chat_request.to_user
        )
        
        return Response({
            'message': 'Chat request accepted',
            'conversation_id': str(conversation.id)
        })
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline chat request"""
        chat_request = self.get_object()
        
        if chat_request.to_user != request.user:
            return Response(
                {'error': 'You can only decline requests sent to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        chat_request.status = 'declined'
        chat_request.responded_at = timezone.now()
        chat_request.save()
        
        return Response({'message': 'Chat request declined'})

class UserConnectionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user connections"""
    serializer_class = UserConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserConnection.objects.filter(
            Q(from_user=self.request.user) | Q(to_user=self.request.user)
        ).select_related('from_user', 'to_user').order_by('-connected_at')

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_messages_read(request):
    """Mark messages as read"""
    message_ids = request.data.get('message_ids', [])
    conversation_id = request.data.get('conversation_id')
    
    if conversation_id:
        # Mark all unread messages in conversation as read
        messages = Message.objects.filter(
            conversation_id=conversation_id,
            conversation__participants=request.user
        ).exclude(sender=request.user).exclude(
            read_receipts__user=request.user  # Exclude already read messages
        )
        
        marked_count = 0
        last_message = None
        
        for message in messages:
            MessageRead.objects.get_or_create(
                message=message,
                user=request.user
            )
            marked_count += 1
            last_message = message
        
        # Get the actual last message in the conversation (not just unread)
        all_messages = Message.objects.filter(
            conversation_id=conversation_id,
            conversation__participants=request.user
        ).order_by('-sent_at').first()
        
        # Update participant's last read
        participant, created = ConversationParticipant.objects.get_or_create(
            conversation_id=conversation_id,
            user=request.user,
            defaults={'joined_at': timezone.now()}
        )
        
        participant.last_read_at = timezone.now()
        participant.last_read_message = all_messages  # Use the latest message overall
        participant.save()
        
        # Send WebSocket notification for read receipts
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f'conversation_{conversation_id}',
                    {
                        'type': 'read_receipt',
                        'user_id': request.user.id,
                        'conversation_id': str(conversation_id),
                        'timestamp': timezone.now().isoformat()
                    }
                )
        except Exception as e:
            # Don't fail if WebSocket notification fails
            pass
        
        return Response({
            'message': f'{marked_count} messages marked as read',
            'marked_count': marked_count,
            'conversation_id': str(conversation_id)
        })
    
    elif message_ids:
        # Mark specific messages as read
        messages = Message.objects.filter(
            id__in=message_ids,
            conversation__participants=request.user
        ).exclude(
            read_receipts__user=request.user  # Exclude already read messages
        )
        
        marked_count = 0
        conversation_ids = set()
        
        for message in messages:
            MessageRead.objects.get_or_create(
                message=message,
                user=request.user
            )
            marked_count += 1
            conversation_ids.add(message.conversation_id)
        
        # Update last read for all affected conversations
        for conv_id in conversation_ids:
            participant, created = ConversationParticipant.objects.get_or_create(
                conversation_id=conv_id,
                user=request.user,
                defaults={'joined_at': timezone.now()}
            )
            
            last_msg = Message.objects.filter(
                conversation_id=conv_id,
                id__in=message_ids
            ).order_by('-sent_at').first()
            
            if last_msg and (not participant.last_read_message or 
                           last_msg.sent_at > participant.last_read_message.sent_at):
                participant.last_read_message = last_msg
                participant.last_read_at = timezone.now()
                participant.save()
        
        return Response({
            'message': f'{marked_count} messages marked as read',
            'marked_count': marked_count
        })
    
    return Response(
        {'error': 'Must provide either message_ids or conversation_id'},
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_read(request):
    """Mark messages as read (alias for mark_messages_read)"""
    return mark_messages_read(request)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_unread_count(request):
    """Get unread message count"""
    unread_count = Message.objects.filter(
        conversation__participants=request.user,
        is_deleted=False
    ).exclude(
        sender=request.user
    ).exclude(
        read_receipts__user=request.user
    ).count()
    
    return Response({'unread_count': unread_count})

class VoiceMessageViewSet(viewsets.ModelViewSet):
    """ViewSet specifically for voice messages"""
    serializer_class = VoiceMessageCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Create a voice message"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.error(f"VoiceMessageViewSet.create called by user: {request.user}")
        logger.error(f"Request FILES: {request.FILES}")
        logger.error(f"Request data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save the voice message
        message = serializer.save()
        
        # Return the message using MessageSerializer for full data
        response_serializer = MessageSerializer(message, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def get_queryset(self):
        """Only allow querying voice messages user has access to"""
        return Message.objects.filter(
            conversation__participants=self.request.user,
            message_type='voice'
        )

class BusinessCardViewSet(viewsets.ModelViewSet):
    """ViewSet for business cards"""
    serializer_class = BusinessCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BusinessCard.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_card(self, request):
        """Get current user's business card"""
        try:
            card = BusinessCard.objects.get(user=request.user)
            serializer = self.get_serializer(card)
            return Response(serializer.data)
        except BusinessCard.DoesNotExist:
            return Response(
                {'error': 'No business card found. Create one first.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def shared_with_me(self, request):
        """Get business cards shared with current user"""
        shared_cards = SharedBusinessCard.objects.filter(
            shared_with=request.user
        ).select_related('card', 'shared_by', 'conversation').order_by('-shared_at')
        
        serializer = SharedBusinessCardSerializer(shared_cards, many=True)
        return Response(serializer.data)

class VideoCallViewSet(viewsets.ModelViewSet):
    """ViewSet for video calls"""
    serializer_class = VideoCallSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get video calls for conversations user participates in"""
        return VideoCall.objects.filter(
            conversation__participants=self.request.user
        ).select_related('conversation', 'caller').prefetch_related('participants').order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Initiate a video call"""
        import uuid as uuid_lib
        
        conversation_id = request.data.get('conversation')
        call_type = request.data.get('call_type', 'video')
        
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants=request.user
            )
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found or you are not a participant'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if there's already an active call
        active_call = VideoCall.objects.filter(
            conversation=conversation,
            status__in=['initiated', 'ringing', 'answered']
        ).first()
        
        if active_call:
            # Check if the call is stale (older than 5 minutes without activity)
            from datetime import timedelta
            stale_time = timezone.now() - timedelta(minutes=5)
            
            if active_call.created_at < stale_time:
                # Auto-end stale call
                active_call.status = 'ended'
                active_call.ended_at = timezone.now()
                active_call.save()
                
                # Update all participants to left
                active_call.call_participants.update(
                    status='left',
                    left_at=timezone.now()
                )
            else:
                # Check if any participants are still active
                active_participants = active_call.call_participants.filter(
                    status__in=['joined', 'invited']
                ).count()
                
                if active_participants == 0:
                    # No active participants, end the call
                    active_call.status = 'ended'
                    active_call.ended_at = timezone.now()
                    active_call.save()
                else:
                    return Response(
                        {'error': 'There is already an active call in this conversation'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        # Create the video call
        video_call = VideoCall.objects.create(
            conversation=conversation,
            caller=request.user,
            call_type=call_type,
            room_id=str(uuid_lib.uuid4()),
            status='initiated'
        )
        
        # Add all participants
        for participant in conversation.participants.all():
            CallParticipant.objects.create(
                call=video_call,
                user=participant,
                status='joined' if participant == request.user else 'invited'
            )
        
        # Create call message
        call_message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=f"📹 {request.user.username} started a {call_type} call",
            message_type='call',
            related_call=video_call
        )
        
        # Send call notification to other participants via WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if channel_layer:
            # Send to the conversation room
            room_group_name = f'chat_{conversation.id}'
            
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'call_notification',
                    'notification_type': 'incoming_call',
                    'call_id': str(video_call.id),
                    'call_data': {
                        'id': str(video_call.id),
                        'call_type': video_call.call_type,
                        'caller': {
                            'id': request.user.id,
                            'username': request.user.username,
                        },
                        'status': video_call.status,
                        'created_at': video_call.created_at.isoformat()
                    },
                    'from_user_id': request.user.id
                }
            )
        
        serializer = self.get_serializer(video_call)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a video call"""
        video_call = self.get_object()
        
        # Check if user is a participant in the conversation
        if not video_call.conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update participant status
        participant, created = CallParticipant.objects.get_or_create(
            call=video_call,
            user=request.user,
            defaults={'status': 'joined', 'joined_at': timezone.now()}
        )
        
        if not created:
            participant.status = 'joined'
            participant.joined_at = timezone.now()
            participant.save()
        
        # Update call status if first participant joins
        if video_call.status == 'initiated':
            video_call.status = 'ringing'
            video_call.save()
        elif video_call.status == 'ringing' and request.user != video_call.caller:
            video_call.status = 'answered'
            video_call.started_at = timezone.now()
            video_call.save()
        
        return Response({
            'message': 'Joined call successfully',
            'room_id': video_call.room_id,
            'call_status': video_call.status
        })
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a video call"""
        video_call = self.get_object()
        
        try:
            participant = CallParticipant.objects.get(
                call=video_call,
                user=request.user
            )
            participant.status = 'left'
            participant.left_at = timezone.now()
            participant.save()
        except CallParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant in this call'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if all participants have left
        active_participants = video_call.call_participants.exclude(
            status__in=['left', 'declined', 'disconnected']
        ).count()
        
        if active_participants == 0:
            video_call.status = 'ended'
            video_call.ended_at = timezone.now()
            video_call.save()
            
            # Create end call message
            Message.objects.create(
                conversation=video_call.conversation,
                sender=request.user,
                content=f"📹 Call ended - Duration: {video_call.duration:.0f} seconds",
                message_type='system',
                related_call=video_call
            )
            
            # Notify all participants that call ended
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            if channel_layer:
                room_group_name = f'chat_{video_call.conversation.id}'
                
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        'type': 'call_notification',
                        'notification_type': 'call_ended',
                        'call_id': str(video_call.id),
                        'call_data': {
                            'id': str(video_call.id),
                            'status': video_call.status,
                            'duration': video_call.duration,
                            'ended_by': request.user.username
                        },
                        'from_user_id': request.user.id
                    }
                )
        
        return Response({
            'message': 'Left call successfully',
            'call_ended': active_participants == 0
        })
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline a video call"""
        video_call = self.get_object()
        
        if request.user == video_call.caller:
            return Response(
                {'error': 'Caller cannot decline their own call'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            participant = CallParticipant.objects.get(
                call=video_call,
                user=request.user
            )
            participant.status = 'declined'
            participant.save()
        except CallParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant in this call'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # If this was a direct call and the other person declined, end the call
        if not video_call.conversation.is_group:
            video_call.status = 'declined'
            video_call.ended_at = timezone.now()
            video_call.save()
        
        # Notify other participants that call was declined
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if channel_layer:
            room_group_name = f'chat_{video_call.conversation.id}'
            
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'call_notification',
                    'notification_type': 'call_declined',
                    'call_id': str(video_call.id),
                    'call_data': {
                        'id': str(video_call.id),
                        'status': video_call.status,
                        'declined_by': request.user.username
                    },
                    'from_user_id': request.user.id
                }
            )
        
        return Response({'message': 'Call declined'})
    
    @action(detail=True, methods=['post'])
    def toggle_video(self, request, pk=None):
        """Toggle video on/off for participant"""
        video_call = self.get_object()
        
        try:
            participant = CallParticipant.objects.get(
                call=video_call,
                user=request.user
            )
            participant.is_video_enabled = not participant.is_video_enabled
            participant.save()
        except CallParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant in this call'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'video_enabled': participant.is_video_enabled
        })
    
    @action(detail=True, methods=['post'])
    def toggle_audio(self, request, pk=None):
        """Toggle audio on/off for participant"""
        video_call = self.get_object()
        
        try:
            participant = CallParticipant.objects.get(
                call=video_call,
                user=request.user
            )
            participant.is_audio_enabled = not participant.is_audio_enabled
            participant.save()
        except CallParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant in this call'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'audio_enabled': participant.is_audio_enabled
        })
    
    @action(detail=True, methods=['post'])
    def rate_quality(self, request, pk=None):
        """Rate call quality after call ends"""
        video_call = self.get_object()
        
        if video_call.status != 'ended':
            return Response(
                {'error': 'Can only rate quality after call ends'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rating = request.data.get('rating')
        if not rating or not (1 <= int(rating) <= 5):
            return Response(
                {'error': 'Rating must be between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        video_call.quality_rating = int(rating)
        video_call.save()
        
        return Response({'message': 'Call quality rated successfully'})
    
    @action(detail=False, methods=['get'])
    def webrtc_config(self, request):
        """Get WebRTC configuration including STUN/TURN servers"""
        # Get configuration from settings
        webrtc_config = getattr(settings, 'WEBRTC_CONFIG', {
            'iceServers': [
                {'urls': 'stun:stun.l.google.com:19302'},
                {'urls': 'stun:stun1.l.google.com:19302'}
            ]
        })
        
        media_constraints = getattr(settings, 'WEBRTC_MEDIA_CONSTRAINTS', {
            'video': {
                'width': {'ideal': 1280},
                'height': {'ideal': 720},
                'frameRate': {'ideal': 30}
            },
            'audio': {
                'echoCancellation': True,
                'noiseSuppression': True,
                'autoGainControl': True
            }
        })
        
        return Response({
            'rtcConfiguration': webrtc_config,
            'mediaConstraints': media_constraints,
            'serverTime': timezone.now().isoformat()
        })
    
    @action(detail=False, methods=['post'])
    def cleanup_stale_calls(self, request):
        """Clean up stale calls for a conversation"""
        conversation_id = request.data.get('conversation_id')
        
        if not conversation_id:
            return Response(
                {'error': 'conversation_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants=request.user
            )
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found or you are not a participant'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Find and clean up stale calls
        from datetime import timedelta
        stale_time = timezone.now() - timedelta(minutes=5)
        
        stale_calls = VideoCall.objects.filter(
            conversation=conversation,
            status__in=['initiated', 'ringing', 'answered'],
            created_at__lt=stale_time
        )
        
        cleaned_count = 0
        for call in stale_calls:
            call.status = 'ended'
            call.ended_at = timezone.now()
            call.save()
            
            # Update all participants to left
            call.call_participants.update(
                status='left',
                left_at=timezone.now()
            )
            cleaned_count += 1
        
        return Response({
            'message': f'Cleaned up {cleaned_count} stale calls',
            'cleaned_count': cleaned_count
        })

class CallSignalViewSet(viewsets.ModelViewSet):
    """ViewSet for WebRTC signaling"""
    serializer_class = CallSignalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get signals for user's calls"""
        return CallSignal.objects.filter(
            call__conversation__participants=self.request.user
        ).select_related('call', 'from_user', 'to_user').order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Create a WebRTC signal"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set from_user automatically
        signal = serializer.save(from_user=request.user)
        
        return Response(self.get_serializer(signal).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending signals for user"""
        signals = CallSignal.objects.filter(
            to_user=request.user,
            processed=False
        ).select_related('call', 'from_user').order_by('created_at')
        
        serializer = self.get_serializer(signals, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_processed(self, request, pk=None):
        """Mark signal as processed"""
        signal = self.get_object()
        
        if signal.to_user != request.user:
            return Response(
                {'error': 'You can only mark your own signals as processed'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        signal.processed = True
        signal.save()
        
        return Response({'message': 'Signal marked as processed'})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_active_call(request, conversation_id):
    """Get active call for a conversation"""
    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )
    except Conversation.DoesNotExist:
        return Response(
            {'error': 'Conversation not found or you are not a participant'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    active_call = VideoCall.objects.filter(
        conversation=conversation,
        status__in=['initiated', 'ringing', 'answered']
    ).first()
    
    if not active_call:
        return Response({'active_call': None})
    
    serializer = VideoCallSerializer(active_call)
    return Response({'active_call': serializer.data})

# Import additional models and serializers
from .models import Poll, PollOption, PollVote, Event, EventAttendee
from .serializers import PollSerializer, PollOptionSerializer, EventSerializer, EventAttendeeSerializer

class PollViewSet(viewsets.ModelViewSet):
    """ViewSet for polls"""
    serializer_class = PollSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only return polls from conversations user participates in
        return Poll.objects.filter(
            conversation__participants=self.request.user
        ).select_related('created_by').prefetch_related('options__votes__user')
    
    def perform_create(self, serializer):
        conversation_id = self.request.data.get('conversation')
        
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants=self.request.user
            )
        except Conversation.DoesNotExist:
            raise serializers.ValidationError('Invalid conversation')
        
        # Create poll
        poll = serializer.save(
            created_by=self.request.user,
            conversation=conversation
        )
        
        # Create poll options
        options_data = self.request.data.get('options', [])
        for i, option_text in enumerate(options_data):
            PollOption.objects.create(
                poll=poll,
                text=option_text,
                order=i
            )
    
    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        """Vote on poll options"""
        poll = self.get_object()
        
        if poll.is_closed or poll.is_expired:
            return Response(
                {'error': 'This poll is closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        option_ids = request.data.get('option_ids', [])
        if not option_ids:
            return Response(
                {'error': 'No options selected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if multiple choice is allowed
        if not poll.multiple_choice and len(option_ids) > 1:
            return Response(
                {'error': 'This poll only allows single choice'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate options belong to this poll
        valid_options = poll.options.filter(id__in=option_ids)
        if valid_options.count() != len(option_ids):
            return Response(
                {'error': 'Invalid poll options'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove existing votes if not multiple choice
        if not poll.multiple_choice:
            PollVote.objects.filter(
                option__poll=poll,
                user=request.user
            ).delete()
        
        # Add new votes
        votes_created = 0
        for option in valid_options:
            vote, created = PollVote.objects.get_or_create(
                option=option,
                user=request.user
            )
            if created:
                votes_created += 1
        
        return Response({
            'message': f'Voted successfully on {votes_created} option(s)',
            'votes_created': votes_created
        })
    
    @action(detail=True, methods=['post'])
    def close_poll(self, request, pk=None):
        """Close a poll (creator only)"""
        poll = self.get_object()
        
        if poll.created_by != request.user:
            return Response(
                {'error': 'Only the poll creator can close it'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        poll.is_closed = True
        poll.closed_at = timezone.now()
        poll.save()
        
        return Response({'message': 'Poll closed successfully'})

class EventViewSet(viewsets.ModelViewSet):
    """ViewSet for events"""
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only return events from conversations user participates in
        return Event.objects.filter(
            conversation__participants=self.request.user
        ).select_related('created_by').prefetch_related('attendees__user')
    
    def perform_create(self, serializer):
        conversation_id = self.request.data.get('conversation')
        
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants=self.request.user
            )
        except Conversation.DoesNotExist:
            raise serializers.ValidationError('Invalid conversation')
        
        event = serializer.save(
            created_by=self.request.user,
            conversation=conversation
        )
        
        # Auto-add creator as attending
        EventAttendee.objects.create(
            event=event,
            user=self.request.user,
            status='going'
        )
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Respond to event invitation"""
        event = self.get_object()
        response_status = request.data.get('status')
        
        if response_status not in ['going', 'maybe', 'not_going']:
            return Response(
                {'error': 'Invalid response status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if event is full (for 'going' status)
        if response_status == 'going' and event.is_full:
            return Response(
                {'error': 'Event is full'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update or create attendance
        attendee, created = EventAttendee.objects.update_or_create(
            event=event,
            user=request.user,
            defaults={'status': response_status}
        )
        
        action = 'created' if created else 'updated'
        return Response({
            'message': f'Response {action} successfully',
            'status': response_status
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an event (creator only)"""
        event = self.get_object()
        
        if event.created_by != request.user:
            return Response(
                {'error': 'Only the event creator can cancel it'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        event.is_cancelled = True
        event.save()
        
        return Response({'message': 'Event cancelled successfully'})