# apps/notifications/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """Get user's notifications with pagination"""
        queryset = self.get_queryset()
        
        # Filter by read status if requested
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Filter by notification type if requested
        notification_type = request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a specific notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'status': f'{updated} notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Delete all notifications for the user"""
        deleted_count = self.get_queryset().delete()[0]
        return Response({'status': f'{deleted_count} notifications deleted'})
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get notification summary"""
        queryset = self.get_queryset()
        
        summary = {
            'total': queryset.count(),
            'unread': queryset.filter(is_read=False).count(),
            'by_type': {}
        }
        
        # Count by type
        for notification_type, display_name in Notification.NOTIFICATION_TYPES:
            count = queryset.filter(notification_type=notification_type).count()
            if count > 0:
                summary['by_type'][notification_type] = {
                    'count': count,
                    'display_name': display_name,
                    'unread': queryset.filter(
                        notification_type=notification_type, 
                        is_read=False
                    ).count()
                }
        
        return Response(summary)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get or create notification preferences for the user"""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preferences
    
    def list(self, request, *args, **kwargs):
        """Get user's notification preferences"""
        preferences = self.get_object()
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update user's notification preferences"""
        preferences = self.get_object()
        serializer = self.get_serializer(preferences, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)