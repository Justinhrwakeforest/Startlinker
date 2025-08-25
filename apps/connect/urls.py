# startup_hub/apps/connect/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileViewSet, FollowViewSet, SpaceViewSet, EventViewSet,
    CofounderMatchViewSet, NotificationViewSet, ResourceTemplateViewSet,
    get_user_stats, search_users, get_trending_users
)

router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'follows', FollowViewSet, basename='follow')
router.register(r'spaces', SpaceViewSet, basename='space')
router.register(r'events', EventViewSet, basename='event')
router.register(r'cofounder-matches', CofounderMatchViewSet, basename='cofounder-match')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'resources', ResourceTemplateViewSet, basename='resource')

urlpatterns = [
    path('', include(router.urls)),
    
    # Additional endpoints
    path('stats/', get_user_stats, name='connect-stats'),
    path('search/', search_users, name='search-users'),
    path('trending/', get_trending_users, name='trending-users'),
]