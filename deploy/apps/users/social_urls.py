# apps/users/social_urls.py - URL patterns for social features
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .social_views import (
    UserFollowViewSet, StoryViewSet, StartupCollaborationViewSet,
    AchievementViewSet, UserAchievementViewSet, ScheduledPostViewSet,
    SocialFeedViewSet, UserMentionViewSet, UserSocialStatsViewSet,
    ProjectTaskViewSet, TaskCommentViewSet, ProjectFileViewSet,
    ProjectMeetingViewSet, ProjectMilestoneViewSet, CollaborationInviteViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'follows', UserFollowViewSet, basename='userfollow')
router.register(r'stories', StoryViewSet, basename='story')
router.register(r'collaborations', StartupCollaborationViewSet, basename='collaboration')
router.register(r'achievements', AchievementViewSet, basename='achievement')
router.register(r'user-achievements', UserAchievementViewSet, basename='userachievement')
router.register(r'scheduled-posts', ScheduledPostViewSet, basename='scheduledpost')
router.register(r'feed', SocialFeedViewSet, basename='socialfeed')
router.register(r'mentions', UserMentionViewSet, basename='usermention')
router.register(r'social-stats', UserSocialStatsViewSet, basename='socialstats')

# Collaboration endpoints
router.register(r'tasks', ProjectTaskViewSet, basename='projecttask')
router.register(r'task-comments', TaskCommentViewSet, basename='taskcomment')
router.register(r'project-files', ProjectFileViewSet, basename='projectfile')
router.register(r'meetings', ProjectMeetingViewSet, basename='projectmeeting')
router.register(r'milestones', ProjectMilestoneViewSet, basename='projectmilestone')
router.register(r'invites', CollaborationInviteViewSet, basename='collaborationinvite')

app_name = 'social'
urlpatterns = [
    path('', include(router.urls)),
]