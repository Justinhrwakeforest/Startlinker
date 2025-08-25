# startup_hub/apps/messaging/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Conversation, Message, MessageRead, ConversationParticipant, VideoCall, CallSignal, CallParticipant
from .serializers import MessageSerializer

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat functionality"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        # Get room_id from URL route
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Get user from scope (set by auth middleware)
        self.user = self.scope["user"]
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if user has access to this conversation
        if not await self.user_has_access():
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept WebSocket connection
        await self.accept()
        
        # Send user online status
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'status': 'online',
                'username': self.user.username
            }
        )
        
        # Update last seen
        await self.update_last_seen()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Send user offline status
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'status': 'offline',
                    'username': self.user.username
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            elif message_type == 'delete_message':
                await self.handle_delete_message(data)
            elif message_type == 'call_signal':
                await self.handle_call_signal(data)
            elif message_type == 'call_status':
                await self.handle_call_status(data)
            elif message_type == 'call_notification':
                await self.handle_call_notification(data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON'
            }))
    
    async def handle_message(self, data):
        """Handle new message"""
        content = data.get('content', '').strip()
        reply_to_id = data.get('reply_to')
        
        if not content:
            await self.send(text_data=json.dumps({
                'error': 'Message content cannot be empty'
            }))
            return
        
        # Save message to database
        message = await self.save_message(content, reply_to_id)
        
        # Serialize message
        message_data = await self.serialize_message(message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )
    
    async def handle_typing(self, data):
        """Handle typing indicator"""
        is_typing = data.get('is_typing', False)
        
        # Send typing status to other users
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': is_typing
            }
        )
    
    async def handle_read_receipt(self, data):
        """Handle read receipt"""
        message_id = data.get('message_id')
        
        if message_id:
            # Mark message as read
            await self.mark_message_read(message_id)
            
            # Send read receipt to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'message_id': message_id,
                    'user_id': self.user.id,
                    'read_at': timezone.now().isoformat()
                }
            )
    
    async def handle_delete_message(self, data):
        """Handle message deletion"""
        message_id = data.get('message_id')
        
        if message_id:
            # Check if user can delete this message
            if await self.can_delete_message(message_id):
                # Mark message as deleted
                await self.delete_message(message_id)
                
                # Send deletion event to room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_deleted',
                        'message_id': message_id,
                        'deleted_by': self.user.id
                    }
                )
    
    # Event handlers for group sends
    async def chat_message(self, event):
        """Send message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def user_status(self, event):
        """Send user status to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'status': event['status'],
            'username': event['username']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send typing indicator to the user who is typing
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    async def read_receipt(self, event):
        """Send read receipt to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'read_at': event['read_at']
        }))
    
    async def message_deleted(self, event):
        """Send message deletion event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id'],
            'deleted_by': event['deleted_by']
        }))
    
    # Database operations
    @database_sync_to_async
    def user_has_access(self):
        """Check if user has access to conversation"""
        try:
            conversation = Conversation.objects.get(id=self.room_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content, reply_to_id=None):
        """Save message to database"""
        conversation = Conversation.objects.get(id=self.room_id)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content,
            reply_to_id=reply_to_id
        )
        
        # Update conversation's updated_at
        conversation.updated_at = timezone.now()
        conversation.save()
        
        # Update participant's last read
        ConversationParticipant.objects.update_or_create(
            conversation=conversation,
            user=self.user,
            defaults={
                'last_read_message': message,
                'last_read_at': timezone.now()
            }
        )
        
        return message
    
    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize message for WebSocket"""
        # Prefetch related data
        message = Message.objects.select_related(
            'sender', 'reply_to', 'reply_to__sender'
        ).prefetch_related('read_receipts').get(id=message.id)
        
        return {
            'id': str(message.id),
            'sender': {
                'id': message.sender.id,
                'username': message.sender.username,
                'display_name': message.sender.get_display_name() if hasattr(message.sender, 'get_display_name') else message.sender.username
            },
            'content': message.content,
            'sent_at': message.sent_at.isoformat(),
            'message_type': message.message_type,
            'voice_file': message.voice_file.url if message.voice_file else None,
            'voice_duration': message.voice_duration,
            'reply_to': {
                'id': str(message.reply_to.id),
                'content': message.reply_to.content[:100],
                'sender': message.reply_to.sender.username
            } if message.reply_to else None,
            'read_by': list(message.read_receipts.values_list('user_id', flat=True)),
            'is_deleted': message.is_deleted
        }
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark message as read"""
        try:
            message = Message.objects.get(id=message_id, conversation_id=self.room_id)
            MessageRead.objects.get_or_create(
                message=message,
                user=self.user
            )
            
            # Update participant's last read
            ConversationParticipant.objects.update_or_create(
                conversation_id=self.room_id,
                user=self.user,
                defaults={
                    'last_read_message': message,
                    'last_read_at': timezone.now()
                }
            )
        except Message.DoesNotExist:
            pass
    
    @database_sync_to_async
    def can_delete_message(self, message_id):
        """Check if user can delete message"""
        try:
            message = Message.objects.get(id=message_id, conversation_id=self.room_id)
            return message.sender == self.user
        except Message.DoesNotExist:
            return False
    
    @database_sync_to_async
    def delete_message(self, message_id):
        """Mark message as deleted"""
        try:
            message = Message.objects.get(id=message_id, conversation_id=self.room_id)
            message.is_deleted = True
            message.deleted_at = timezone.now()
            message.save()
        except Message.DoesNotExist:
            pass
    
    async def handle_call_signal(self, data):
        """Handle WebRTC signaling for video calls"""
        signal_type = data.get('signal_type')
        signal_data = data.get('signal_data')
        to_user_id = data.get('to_user_id')
        call_id = data.get('call_id')
        
        if not all([signal_type, signal_data, call_id]):
            await self.send(text_data=json.dumps({
                'error': 'Missing required signal data'
            }))
            return
        
        # Save signal to database
        await self.save_call_signal(call_id, to_user_id, signal_type, signal_data)
        
        # Send signal to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'call_signal',
                'signal_type': signal_type,
                'signal_data': signal_data,
                'from_user_id': self.user.id,
                'to_user_id': to_user_id,
                'call_id': call_id
            }
        )
    
    async def handle_call_status(self, data):
        """Handle call status updates"""
        call_id = data.get('call_id')
        status = data.get('status')
        
        if not call_id or not status:
            return
        
        # Update call status
        await self.update_call_status(call_id, status)
        
        # Send status update to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'call_status_update',
                'call_id': call_id,
                'status': status,
                'user_id': self.user.id
            }
        )
    
    async def handle_call_notification(self, data):
        """Handle call notifications (incoming call, call ended, etc.)"""
        notification_type = data.get('notification_type')
        call_id = data.get('call_id')
        call_data = data.get('call_data', {})
        
        if not all([notification_type, call_id]):
            return
        
        # Send notification to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'call_notification',
                'notification_type': notification_type,
                'call_id': call_id,
                'call_data': call_data,
                'from_user_id': self.user.id
            }
        )
    
    # Event handlers for group sends
    async def call_signal(self, event):
        """Send call signal to WebSocket"""
        # Only send to the target user
        if event.get('to_user_id') == self.user.id or event.get('from_user_id') == self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'call_signal',
                'signal_type': event['signal_type'],
                'signal_data': event['signal_data'],
                'from_user_id': event['from_user_id'],
                'to_user_id': event.get('to_user_id'),
                'call_id': event['call_id']
            }))
    
    async def call_status_update(self, event):
        """Send call status update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'call_status_update',
            'call_id': event['call_id'],
            'status': event['status'],
            'user_id': event['user_id']
        }))
    
    async def call_notification(self, event):
        """Send call notification to WebSocket"""
        # Don't send notification to the user who initiated it
        if event['from_user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'call_notification',
                'notification_type': event['notification_type'],
                'call_id': event['call_id'],
                'call_data': event['call_data'],
                'from_user_id': event['from_user_id']
            }))
    
    @database_sync_to_async
    def save_call_signal(self, call_id, to_user_id, signal_type, signal_data):
        """Save call signal to database"""
        try:
            call = VideoCall.objects.get(id=call_id)
            to_user = None
            if to_user_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                to_user = User.objects.get(id=to_user_id)
            
            CallSignal.objects.create(
                call=call,
                from_user=self.user,
                to_user=to_user,
                signal_type=signal_type,
                signal_data=signal_data
            )
        except (VideoCall.DoesNotExist, Exception) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving call signal: {e}")
    
    @database_sync_to_async
    def update_call_status(self, call_id, status):
        """Update call status"""
        try:
            call = VideoCall.objects.get(id=call_id)
            
            # Update call status
            if status == 'started' and not call.started_at:
                call.status = 'answered'
                call.started_at = timezone.now()
            elif status == 'ended':
                call.status = 'ended'
                call.ended_at = timezone.now()
            
            call.save()
        except VideoCall.DoesNotExist:
            pass
    
    @database_sync_to_async
    def update_last_seen(self):
        """Update user's last seen timestamp"""
        # This could be extended to track online status
        pass