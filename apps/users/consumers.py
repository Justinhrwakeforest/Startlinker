# apps/users/consumers.py - WebSocket consumer for real-time achievement updates
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

class AchievementConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Connect user to their personal achievement channel"""
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Join user-specific achievement group
        self.achievement_group_name = f"achievements_{self.user.id}"
        await self.channel_layer.group_add(
            self.achievement_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current achievement count on connection
        await self.send_achievement_count()
    
    async def disconnect(self, close_code):
        """Disconnect from achievement channel"""
        if hasattr(self, 'achievement_group_name'):
            await self.channel_layer.group_discard(
                self.achievement_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'get_achievement_count':
                await self.send_achievement_count()
            elif message_type == 'mark_notification_read':
                notification_id = text_data_json.get('notification_id')
                await self.mark_notification_read(notification_id)
        except json.JSONDecodeError:
            pass
    
    async def achievement_earned(self, event):
        """Send achievement earned notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'achievement_earned',
            'achievement': event['achievement_data'],
            'notification_id': event['notification_id']
        }))
    
    async def achievement_progress(self, event):
        """Send achievement progress update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'achievement_progress',
            'achievement_slug': event['achievement_slug'],
            'progress_percentage': event['progress_percentage'],
            'current_progress': event['current_progress']
        }))
    
    @database_sync_to_async
    def get_achievement_count(self):
        """Get user's total achievement count"""
        from .social_models import UserAchievement
        return UserAchievement.objects.filter(user=self.user).count()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark achievement notification as read"""
        try:
            from apps.notifications.models import Notification
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user,
                notification_type='achievement_earned'
            )
            notification.is_read = True
            notification.save()
            return True
        except:
            return False
    
    async def send_achievement_count(self):
        """Send current achievement count to WebSocket"""
        count = await self.get_achievement_count()
        await self.send(text_data=json.dumps({
            'type': 'achievement_count',
            'count': count
        }))

# Utility function to send real-time updates
def send_achievement_update(user_id, achievement_data, notification_id=None):
    """Send real-time achievement update via WebSocket"""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f"achievements_{user_id}",
            {
                'type': 'achievement_earned',
                'achievement_data': achievement_data,
                'notification_id': notification_id
            }
        )

def send_progress_update(user_id, achievement_slug, progress_percentage, current_progress):
    """Send real-time progress update via WebSocket"""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f"achievements_{user_id}",
            {
                'type': 'achievement_progress',
                'achievement_slug': achievement_slug,
                'progress_percentage': progress_percentage,
                'current_progress': current_progress
            }
        )