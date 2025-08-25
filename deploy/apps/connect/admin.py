# startup_hub/apps/connect/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import (
    UserProfile, Follow, Space, SpaceMembership, Event, EventRegistration,
    CofounderMatch, MatchScore, ResourceTemplate, Notification
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'headline', 'reputation_score', 'follower_count', 
        'following_count', 'is_online_display', 'last_seen', 'created_at'
    ]
    list_filter = ['is_open_to_opportunities', 'show_online_status', 'created_at']
    search_fields = ['user__username', 'user__email', 'headline', 'expertise']
    readonly_fields = [
        'reputation_score', 'helpful_votes', 'follower_count', 
        'following_count', 'last_seen', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'avatar_url', 'headline')
        }),
        ('Professional Info', {
            'fields': ('expertise', 'looking_for', 'is_open_to_opportunities', 'preferred_contact_method')
        }),
        ('Social Links', {
            'fields': ('linkedin_url', 'twitter_handle', 'github_username', 'personal_website')
        }),
        ('Metrics', {
            'fields': ('reputation_score', 'helpful_votes', 'follower_count', 'following_count', 'badges')
        }),
        ('Settings', {
            'fields': (
                'show_online_status', 'allow_direct_messages', 
                'email_on_mention', 'email_on_reply', 'email_on_follow'
            )
        }),
        ('Timestamps', {
            'fields': ('last_seen', 'created_at', 'updated_at')
        })
    )
    
    def user_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:users_user_change', args=[obj.user.pk]),
            obj.user.username
        )
    user_link.short_description = 'User'
    
    def is_online_display(self, obj):
        if obj.is_online:
            return format_html('<span style="color: green;">●</span> Online')
        return format_html('<span style="color: gray;">●</span> Offline')
    is_online_display.short_description = 'Status'

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']
    date_hierarchy = 'created_at'

@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'icon', 'space_type', 'member_count', 
        'post_count', 'created_by', 'created_at'
    ]
    list_filter = ['space_type', 'auto_approve_members', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['member_count', 'post_count', 'created_at', 'updated_at']
    filter_horizontal = ['moderators']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'description', 'icon', 'cover_image_url')
        }),
        ('Settings', {
            'fields': (
                'space_type', 'auto_approve_members', 
                'allow_member_posts', 'require_post_approval'
            )
        }),
        ('Management', {
            'fields': ('created_by', 'moderators')
        }),
        ('Metrics', {
            'fields': ('member_count', 'post_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )

@admin.register(SpaceMembership)
class SpaceMembershipAdmin(admin.ModelAdmin):
    list_display = [
        'space', 'user', 'role', 'is_approved', 
        'is_banned', 'joined_at'
    ]
    list_filter = ['role', 'is_approved', 'is_banned', 'joined_at']
    search_fields = ['space__name', 'user__username']
    date_hierarchy = 'joined_at'
    
    actions = ['approve_memberships', 'ban_users', 'unban_users']
    
    def approve_memberships(self, request, queryset):
        count = queryset.filter(is_approved=False).update(is_approved=True)
        self.message_user(request, f'{count} memberships approved.')
    approve_memberships.short_description = "Approve selected memberships"
    
    def ban_users(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(is_banned=True, banned_at=timezone.now())
        self.message_user(request, f'{count} users banned.')
    ban_users.short_description = "Ban selected users"
    
    def unban_users(self, request, queryset):
        count = queryset.update(is_banned=False, banned_at=None, banned_reason='')
        self.message_user(request, f'{count} users unbanned.')
    unban_users.short_description = "Unban selected users"

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'event_type', 'start_datetime', 'is_online',
        'attendee_count', 'is_upcoming', 'is_published', 'host'
    ]
    list_filter = [
        'event_type', 'is_online', 'is_published', 
        'is_cancelled', 'start_datetime'
    ]
    search_fields = ['title', 'description', 'host__username']
    date_hierarchy = 'start_datetime'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Event Info', {
            'fields': ('title', 'description', 'event_type')
        }),
        ('Schedule', {
            'fields': ('start_datetime', 'end_datetime', 'timezone')
        }),
        ('Location', {
            'fields': ('is_online', 'location', 'meeting_url')
        }),
        ('Organization', {
            'fields': ('host', 'space')
        }),
        ('Registration', {
            'fields': (
                'requires_registration', 'max_attendees', 
                'registration_deadline'
            )
        }),
        ('Status', {
            'fields': ('is_published', 'is_cancelled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def attendee_count(self, obj):
        return obj.registrations.filter(status='registered').count()
    attendee_count.short_description = 'Attendees'

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        'event', 'user', 'status', 'registered_at'
    ]
    list_filter = ['status', 'registered_at']
    search_fields = ['event__title', 'user__username']
    date_hierarchy = 'registered_at'
    
    actions = ['mark_attended', 'mark_no_show']
    
    def mark_attended(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(status='registered').update(
            status='attended',
            attended_at=timezone.now()
        )
        self.message_user(request, f'{count} registrations marked as attended.')
    mark_attended.short_description = "Mark as attended"
    
    def mark_no_show(self, request, queryset):
        count = queryset.filter(status='registered').update(status='no_show')
        self.message_user(request, f'{count} registrations marked as no-show.')
    mark_no_show.short_description = "Mark as no-show"

@admin.register(CofounderMatch)
class CofounderMatchAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'commitment_level', 'startup_stage_preference',
        'experience_years', 'is_active', 'created_at'
    ]
    list_filter = [
        'commitment_level', 'startup_stage_preference', 
        'is_active', 'experience_years'
    ]
    search_fields = ['user__username', 'bio', 'skills']
    filter_horizontal = ['industry_preferences']
    
    fieldsets = (
        ('User', {
            'fields': ('user', 'is_active')
        }),
        ('What They Bring', {
            'fields': (
                'skills', 'experience_years', 'commitment_level', 
                'equity_expectation'
            )
        }),
        ('What They Want', {
            'fields': (
                'looking_for_skills', 'startup_stage_preference', 
                'industry_preferences'
            )
        }),
        ('About', {
            'fields': ('bio', 'achievements', 'ideal_cofounder')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )

@admin.register(ResourceTemplate)
class ResourceTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'is_premium', 'download_count',
        'contributed_by', 'created_at'
    ]
    list_filter = ['category', 'is_premium', 'created_at']
    search_fields = ['title', 'description', 'tags']
    readonly_fields = ['download_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'category')
        }),
        ('Content', {
            'fields': ('content', 'file_url', 'preview_image_url')
        }),
        ('Metadata', {
            'fields': ('tags', 'is_premium', 'download_count')
        }),
        ('Attribution', {
            'fields': ('contributed_by',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'notification_type', 'title', 'is_read',
        'created_at', 'from_user'
    ]
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'read_at']
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        self.message_user(request, f'{count} notifications marked as read.')
    mark_as_read.short_description = "Mark as read"
    
    def mark_as_unread(self, request, queryset):
        count = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{count} notifications marked as unread.')
    mark_as_unread.short_description = "Mark as unread"

# Register inline admin for better UX
class SpaceMembershipInline(admin.TabularInline):
    model = SpaceMembership
    extra = 0
    fields = ['user', 'role', 'is_approved', 'joined_at']
    readonly_fields = ['joined_at']

class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 0
    fields = ['user', 'status', 'registered_at']
    readonly_fields = ['registered_at']

# Add inlines to main admins
SpaceAdmin.inlines = [SpaceMembershipInline]
EventAdmin.inlines = [EventRegistrationInline]