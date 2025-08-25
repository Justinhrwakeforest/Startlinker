# startup_hub/apps/messaging/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConversationViewSet, MessageViewSet, ChatRequestViewSet,
    UserConnectionViewSet, BusinessCardViewSet, VoiceMessageViewSet,
    VideoCallViewSet, CallSignalViewSet,
    mark_messages_read, mark_read, get_unread_count, get_active_call
)

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'voice-messages', VoiceMessageViewSet, basename='voice-message')
router.register(r'chat-requests', ChatRequestViewSet, basename='chat-request')
router.register(r'connections', UserConnectionViewSet, basename='connection')
router.register(r'business-cards', BusinessCardViewSet, basename='business-card')
router.register(r'video-calls', VideoCallViewSet, basename='video-call')
router.register(r'call-signals', CallSignalViewSet, basename='call-signal')

urlpatterns = [
    path('', include(router.urls)),
    
    # Additional endpoints
    path('mark-read/', mark_read, name='mark-read'),
    path('mark-messages-read/', mark_messages_read, name='mark-messages-read'),
    path('unread-count/', get_unread_count, name='unread-count'),
    path('conversations/<uuid:conversation_id>/active-call/', get_active_call, name='active-call'),
]